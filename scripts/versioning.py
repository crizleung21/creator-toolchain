#!/usr/bin/env python3
"""Single-source version management for Creator Toolchain."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    from creator_transactions import atomic_write_json, atomic_write_text
except ImportError:  # pragma: no cover
    from scripts.creator_transactions import atomic_write_json, atomic_write_text

VERSION_PATH = Path("VERSION")
MANIFEST_PATH = Path("plugin/creator-toolchain/.codex-plugin/plugin.json")
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$")


class VersionError(RuntimeError):
    """Raised when version state is invalid or divergent."""


def validate_version(value: str) -> str:
    value = value.strip()
    if not SEMVER_RE.fullmatch(value):
        raise VersionError(f"invalid semantic version: {value!r}")
    return value


def read_version(root: Path) -> str:
    path = Path(root).resolve() / VERSION_PATH
    try:
        return validate_version(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise VersionError(f"cannot read {VERSION_PATH}: {exc}") from exc


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VersionError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VersionError(f"JSON root must be an object: {path}")
    return value


def check_version_bindings(root: Path) -> list[str]:
    root = Path(root).resolve()
    findings: list[str] = []
    try:
        version = read_version(root)
    except VersionError as exc:
        return [str(exc)]
    manifest_path = root / MANIFEST_PATH
    try:
        manifest = _load_json(manifest_path)
    except VersionError as exc:
        findings.append(str(exc))
    else:
        if manifest.get("version") != version:
            findings.append(
                f"{MANIFEST_PATH}: version={manifest.get('version')!r} expected={version!r}"
            )
    return findings


def synchronize_version(root: Path, version: str, *, write: bool) -> list[str]:
    """Synchronize derived version bindings from the authoritative VERSION value."""

    root = Path(root).resolve()
    version = validate_version(version)
    version_path = root / VERSION_PATH
    manifest_path = root / MANIFEST_PATH
    manifest = _load_json(manifest_path)
    manifest["version"] = version
    if write:
        atomic_write_text(version_path, version + "\n", mode=0o644)
        atomic_write_json(manifest_path, manifest, mode=0o644)
    return check_version_bindings(root) if write else (
        [] if read_version(root) == version and _load_json(manifest_path).get("version") == version
        else ["version bindings differ from the requested version"]
    )
