#!/usr/bin/env python3
"""Load, validate, and inspect the canonical Creator Toolchain state-surface registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_RELATIVE = Path("config/surface-registry.json")
EXPECTED_PATHS = (
    ".creator/workspace.json",
    ".creator/projects.json",
    ".creator/entities.json",
    ".creator/state.json",
    ".creator/session-insights.json",
    ".creator/operator.json",
    ".creator/backlog.json",
    ".creator/surfaces.json",
    ".creator/decisions.json",
    ".creator/rules.json",
)
REQUIRED_FIELDS = {"surface_id", "path", "schema", "owner_skill", "privacy_class", "required", "mutable", "archive_policy"}
PRIVACY_CLASSES = {"publishable_template", "repository_workflow_state", "private", "repository_contract"}
ARCHIVE_POLICIES = {"retain", "archive", "replace"}


class SurfaceRegistryError(ValueError):
    """Raised when the canonical surface registry is invalid."""


def load_registry_document(root: Path = ROOT) -> dict[str, Any]:
    path = Path(root) / REGISTRY_RELATIVE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SurfaceRegistryError(f"cannot load surface registry: {exc}") from exc
    if not isinstance(value, dict):
        raise SurfaceRegistryError("surface registry root must be an object")
    if value.get("schema_version") != "1.0.0":
        raise SurfaceRegistryError("surface registry schema_version must be 1.0.0")
    if value.get("state_schema_version") != "0.4.0":
        raise SurfaceRegistryError("surface registry state_schema_version must be 0.4.0")
    for field in ("created_at", "updated_at"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise SurfaceRegistryError(f"surface registry {field} must be non-empty")
    return value


def load_surface_registry(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    document = load_registry_document(root)
    items = document.get("surfaces")
    if not isinstance(items, list):
        raise SurfaceRegistryError("surface registry surfaces must be an array")
    by_path: dict[str, dict[str, Any]] = {}
    ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise SurfaceRegistryError(f"surfaces[{index}] must be an object")
        if set(item) != REQUIRED_FIELDS:
            missing = sorted(REQUIRED_FIELDS - set(item))
            extra = sorted(set(item) - REQUIRED_FIELDS)
            raise SurfaceRegistryError(f"surfaces[{index}] fields invalid; missing={missing}, extra={extra}")
        surface_id = item.get("surface_id")
        path = item.get("path")
        if not isinstance(surface_id, str) or not surface_id:
            raise SurfaceRegistryError(f"surfaces[{index}].surface_id is invalid")
        if surface_id in ids:
            raise SurfaceRegistryError(f"duplicate surface_id: {surface_id}")
        ids.add(surface_id)
        if not isinstance(path, str) or path not in EXPECTED_PATHS:
            raise SurfaceRegistryError(f"surfaces[{index}].path is invalid: {path!r}")
        if path in by_path:
            raise SurfaceRegistryError(f"duplicate surface path: {path}")
        if item.get("schema") != f"schemas/workspace/{Path(path).stem}.schema.json":
            raise SurfaceRegistryError(f"surface schema mismatch: {path}")
        expected_owner = "creator-rule-router" if path == ".creator/rules.json" else "creator-workspace-manager"
        if item.get("owner_skill") != expected_owner:
            raise SurfaceRegistryError(f"surface owner mismatch: {path}")
        if item.get("privacy_class") not in PRIVACY_CLASSES:
            raise SurfaceRegistryError(f"surface privacy_class is invalid: {path}")
        if item.get("required") is not True or item.get("mutable") is not True:
            raise SurfaceRegistryError(f"surface required/mutable contract is invalid: {path}")
        if item.get("archive_policy") not in ARCHIVE_POLICIES:
            raise SurfaceRegistryError(f"surface archive_policy is invalid: {path}")
        by_path[path] = dict(item)
    if tuple(by_path) != EXPECTED_PATHS:
        raise SurfaceRegistryError(f"surface registry must contain the canonical ordered paths; found {tuple(by_path)}")
    return by_path


def state_files(root: Path = ROOT) -> tuple[str, ...]:
    return tuple(load_surface_registry(root))


def registry_summary(root: Path = ROOT) -> dict[str, Any]:
    document = load_registry_document(root)
    surfaces = list(load_surface_registry(root).values())
    return {
        "schema_version": document["schema_version"],
        "state_schema_version": document["state_schema_version"],
        "surface_count": len(surfaces),
        "surfaces": surfaces,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "validate", "get"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.command == "get":
            if not args.path:
                raise SurfaceRegistryError("get requires --path")
            registry = load_surface_registry(args.root)
            if args.path not in registry:
                raise SurfaceRegistryError(f"unknown canonical surface: {args.path}")
            result: Any = registry[args.path]
        else:
            result = registry_summary(args.root)
    except (SurfaceRegistryError, OSError) as exc:
        print(f"Creator surface registry failed: {exc}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(f"Validated {result['surface_count']} canonical state surfaces.")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
