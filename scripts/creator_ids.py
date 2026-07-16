#!/usr/bin/env python3
"""Deterministic identifier helpers for Creator Toolchain state."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

PREFIX_RE = re.compile(r"^[A-Z][A-Z0-9]{1,15}$")
ID_RE = re.compile(r"^(?P<prefix>[A-Z][A-Z0-9]{1,15})-(?P<body>[A-F0-9]{8,64})$")


class CreatorIdError(ValueError):
    """Raised when an identifier cannot be created or validated."""


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def deterministic_id(prefix: str, *parts: Any, length: int = 12) -> str:
    """Create a stable ID from a prefix and canonicalized input parts."""

    if not PREFIX_RE.fullmatch(prefix):
        raise CreatorIdError(f"invalid ID prefix: {prefix!r}")
    if not 8 <= length <= 64:
        raise CreatorIdError("length must be between 8 and 64")
    digest = hashlib.sha256(_canonical(parts)).hexdigest().upper()[:length]
    return f"{prefix}-{digest}"


def validate_id(value: str, *, prefix: str | None = None) -> str:
    """Validate and return a Creator Toolchain identifier."""

    match = ID_RE.fullmatch(value)
    if not match:
        raise CreatorIdError(f"invalid identifier: {value!r}")
    if prefix is not None and match.group("prefix") != prefix:
        raise CreatorIdError(f"identifier prefix must be {prefix!r}")
    return value
