#!/usr/bin/env python3
"""Load and validate Creator Toolchain project-type contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_RELATIVE = Path("config/project-types.json")
REQUIRED_FIELDS = {
    "type_id",
    "rigor",
    "purpose",
    "inputs",
    "deliverables",
    "acceptance_patterns",
    "risk_checklist",
    "rule_domains",
    "audit_domains",
    "default_handoff",
    "example",
}
EXPECTED_TYPES = {
    "slide-deck",
    "ai-image-system",
    "characterlock-system",
    "headlock-system",
    "ai-video-system",
    "prompt-pack",
    "character-registry",
    "content-campaign",
    "creator-tooling",
    "application",
    "workflow",
    "utility",
    "research-system",
}


class ProjectTypeError(ValueError):
    """Raised when the project-type registry is invalid."""


def load_project_types(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    path = Path(root) / REGISTRY_RELATIVE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectTypeError(f"cannot load project-type registry: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "1.0.0":
        raise ProjectTypeError("project-type registry schema_version must be 1.0.0")
    items = value.get("project_types")
    if not isinstance(items, list):
        raise ProjectTypeError("project_types must be an array")
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ProjectTypeError(f"project_types[{index}] must be an object")
        missing = sorted(REQUIRED_FIELDS - set(item))
        if missing:
            raise ProjectTypeError(f"project type at index {index} is missing {missing}")
        type_id = item.get("type_id")
        if not isinstance(type_id, str) or not type_id:
            raise ProjectTypeError(f"project_types[{index}].type_id is invalid")
        if type_id in result:
            raise ProjectTypeError(f"duplicate project type: {type_id}")
        for list_field in (
            "inputs",
            "deliverables",
            "acceptance_patterns",
            "risk_checklist",
            "rule_domains",
            "audit_domains",
        ):
            field_value = item.get(list_field)
            if not isinstance(field_value, list) or not field_value or not all(
                isinstance(entry, str) and entry.strip() for entry in field_value
            ):
                raise ProjectTypeError(f"{type_id}.{list_field} must be a non-empty string array")
        if item.get("default_handoff") != "creator-execution-cycle":
            raise ProjectTypeError(f"{type_id}.default_handoff must be creator-execution-cycle")
        result[type_id] = item
    if set(result) != EXPECTED_TYPES:
        raise ProjectTypeError(
            f"project-type registry must contain exactly {sorted(EXPECTED_TYPES)}; found {sorted(result)}"
        )
    return result


def get_project_type(type_id: str, root: Path = ROOT) -> dict[str, Any]:
    try:
        return load_project_types(root)[type_id]
    except KeyError as exc:
        raise ProjectTypeError(f"unknown project type: {type_id}") from exc
