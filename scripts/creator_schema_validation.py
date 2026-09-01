#!/usr/bin/env python3
"""Workspace and arbitrary JSON Schema validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import creator_schema_validation_impl as _impl
    from json_schema_lite import load_schema, validate as _validate_schema
except ImportError:  # pragma: no cover
    from scripts import creator_schema_validation_impl as _impl
    from scripts.json_schema_lite import load_schema, validate as _validate_schema

for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)


def validate_json_document(schema_path: Path, value: Any) -> list[str]:
    """Validate any JSON-compatible value against one repository schema file."""

    return _validate_schema(value, load_schema(Path(schema_path)))
