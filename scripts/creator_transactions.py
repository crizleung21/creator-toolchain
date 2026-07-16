#!/usr/bin/env python3
"""Atomic write primitives used by Creator Toolchain state operations."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Callable


class TransactionError(RuntimeError):
    """Raised when an atomic state transaction fails."""


def _reject_symlink_target(path: Path) -> None:
    if path.is_symlink():
        raise TransactionError(f"refusing to replace symbolic link: {path}")
    current = path.parent
    while current != current.parent:
        if current.exists() and current.is_symlink():
            raise TransactionError(f"refusing symbolic-link parent: {current}")
        current = current.parent


def atomic_write_bytes(
    path: Path,
    data: bytes,
    *,
    validator: Callable[[Path], None] | None = None,
    mode: int | None = None,
) -> None:
    """Write bytes atomically and restore the original file on validation failure."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_target(path)

    original_exists = path.exists()
    original_bytes = path.read_bytes() if original_exists else None
    original_mode = stat.S_IMODE(path.stat().st_mode) if original_exists else None
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode if mode is not None else (original_mode or 0o600))
        os.replace(temporary_path, path)
        temporary_path = None
        if validator is not None:
            validator(path)
    except Exception as exc:
        try:
            if original_exists and original_bytes is not None:
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".rollback", delete=False) as handle:
                    rollback = Path(handle.name)
                    handle.write(original_bytes)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(rollback, original_mode or 0o600)
                os.replace(rollback, path)
            elif path.exists():
                path.unlink()
        except Exception as rollback_exc:  # pragma: no cover
            raise TransactionError(f"write failed and rollback failed: {rollback_exc}") from exc
        raise TransactionError(str(exc)) from exc
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def atomic_write_text(
    path: Path,
    text: str,
    *,
    validator: Callable[[Path], None] | None = None,
    mode: int | None = None,
) -> None:
    atomic_write_bytes(path, text.encode("utf-8"), validator=validator, mode=mode)


def atomic_write_json(
    path: Path,
    value: Any,
    *,
    validator: Callable[[Path], None] | None = None,
    mode: int | None = None,
) -> None:
    text = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    atomic_write_text(path, text, validator=validator, mode=mode)
