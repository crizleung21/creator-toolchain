#!/usr/bin/env python3
"""Prepare Creator Toolchain state for migration from schema 0.3.0 to 0.4.0.

This first Phase 1 slice implements deterministic planning and backup generation.
The live write migration remains intentionally disabled until migration fixtures and
rollback gates are added in the next Phase 1 execution cycle.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_state_store import STATE_FILES, safe_path
except ImportError:  # pragma: no cover
    from scripts.creator_state_store import STATE_FILES, safe_path

SOURCE_SCHEMA = "0.3.0"
TARGET_SCHEMA = "0.4.0"
PRIVACY_MAP = {"local_private": "private", "local/private": "repository_workflow_state"}


class MigrationError(RuntimeError):
    """Raised when migration planning cannot proceed safely."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def migrate_value(relative: str, value: dict[str, Any], *, timestamp: str) -> dict[str, Any]:
    migrated = json.loads(json.dumps(value))
    if migrated.get("schema_version") != SOURCE_SCHEMA:
        raise MigrationError(f"{relative}: expected schema {SOURCE_SCHEMA}")
    migrated["schema_version"] = TARGET_SCHEMA
    migrated["privacy_class"] = PRIVACY_MAP.get(migrated.get("privacy_class"), migrated.get("privacy_class"))
    migrated.setdefault("created_at", timestamp)
    migrated["updated_at"] = timestamp
    return migrated


def build_migration_plan(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    timestamp = _timestamp()
    files: list[dict[str, Any]] = []
    for relative in STATE_FILES:
        path = safe_path(root, relative)
        if not path.is_file():
            raise MigrationError(f"missing state file: {relative}")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MigrationError(f"{relative}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise MigrationError(f"{relative}: root must be an object")
        migrated = migrate_value(relative, value, timestamp=timestamp)
        files.append({"path": relative, "source_schema": SOURCE_SCHEMA, "target_schema": TARGET_SCHEMA, "changed_fields": sorted(key for key in migrated if migrated.get(key) != value.get(key))})
    return {"schema_version": "1.0.0", "source_schema": SOURCE_SCHEMA, "target_schema": TARGET_SCHEMA, "generated_at": timestamp, "write_enabled": False, "files": files}


def write_backup(root: Path, destination: Path) -> None:
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    if destination.exists():
        raise MigrationError(f"backup destination already exists: {destination}")
    destination.mkdir(parents=True)
    for relative in STATE_FILES:
        source = safe_path(root, relative)
        shutil.copy2(source, destination / Path(relative).name)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.write:
        print("Live migration is gated until the next Phase 1 cycle.", file=sys.stderr)
        return 2
    try:
        plan = build_migration_plan(args.root)
        if args.backup:
            write_backup(args.root, args.backup)
        text = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
        if args.plan:
            args.plan.parent.mkdir(parents=True, exist_ok=True)
            args.plan.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    except (MigrationError, OSError) as exc:
        print(f"Migration planning failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
