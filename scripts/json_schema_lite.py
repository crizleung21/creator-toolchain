#!/usr/bin/env python3
"""Small dependency-free validator for the JSON Schema subset used by Creator Toolchain."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class JsonSchemaError(ValueError):
    """Raised when a schema document is invalid or unsupported."""


def load_schema(path: Path) -> dict[str, Any]:
    try:
        schema = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JsonSchemaError(f"cannot load schema {path}: {exc}") from exc
    if not isinstance(schema, dict):
        raise JsonSchemaError(f"schema root must be an object: {path}")
    return schema


def _type_matches(instance: Any, expected: str) -> bool:
    if expected == "null":
        return instance is None
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "object":
        return isinstance(instance, dict)
    raise JsonSchemaError(f"unsupported schema type: {expected}")


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate(instance: Any, schema: dict[str, Any], *, path: str = "$") -> list[str]:
    """Return deterministic validation findings for the supported schema subset."""

    findings: list[str] = []

    if "const" in schema and instance != schema["const"]:
        findings.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        findings.append(f"{path}: must be one of {schema['enum']!r}")

    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = [expected_type] if isinstance(expected_type, str) else expected_type
        if not isinstance(expected_types, list) or not all(isinstance(item, str) for item in expected_types):
            raise JsonSchemaError(f"{path}: invalid type declaration")
        if not any(_type_matches(instance, item) for item in expected_types):
            findings.append(f"{path}: invalid type; expected {expected_types!r}")
            return findings

    if isinstance(instance, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(instance) < minimum:
            findings.append(f"{path}: length must be at least {minimum}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, instance) is None:
            findings.append(f"{path}: must match {pattern!r}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and instance < minimum:
            findings.append(f"{path}: must be >= {minimum}")

    if isinstance(instance, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(instance) < minimum:
            findings.append(f"{path}: must contain at least {minimum} items")
        if schema.get("uniqueItems") is True:
            keys = [_json_key(item) for item in instance]
            if len(keys) != len(set(keys)):
                findings.append(f"{path}: array items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                findings.extend(validate(item, item_schema, path=f"{path}[{index}]"))

    if isinstance(instance, dict):
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise JsonSchemaError(f"{path}: required must be an array")
        for key in required:
            if key not in instance:
                findings.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise JsonSchemaError(f"{path}: properties must be an object")
        for key, value in instance.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                findings.extend(validate(value, child_schema, path=f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                findings.append(f"{path}: unexpected property {key!r}")

    return findings
