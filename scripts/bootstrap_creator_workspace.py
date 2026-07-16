#!/usr/bin/env python3
"""Create or validate a Creator Toolchain schema 0.4.0 workspace."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_state_store import STATE_FILES, StateStoreError, load_json, safe_path, validate_workspace
    from creator_transactions import atomic_write_json, atomic_write_text
except ImportError:  # pragma: no cover
    from scripts.creator_state_store import STATE_FILES, StateStoreError, load_json, safe_path, validate_workspace
    from scripts.creator_transactions import atomic_write_json, atomic_write_text

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "templates/workspace"
ARCHITECTURE_TEMPLATE = """# Creator Workspace Architecture\n\nThis repository uses Creator Toolchain workspace state schema `0.4.0`.\n\n- State surfaces: `.creator/*.json`\n- Workspace owner: `creator-workspace-manager`\n- Rules owner: `creator-rule-router`\n- State mutations must be validated and atomic.\n"""


class BootstrapError(RuntimeError):
    """Raised when a workspace cannot be bootstrapped safely."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _render(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _render(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_render(item, replacements) for item in value]
    if isinstance(value, str):
        for token, replacement in replacements.items():
            value = value.replace(token, replacement)
    return value


def _template_path(relative: str) -> Path:
    return TEMPLATE_ROOT / Path(relative).name


def planned_changes(root: Path) -> list[str]:
    root = Path(root).resolve()
    changes: list[str] = []
    for relative in STATE_FILES:
        if not safe_path(root, relative).exists():
            changes.append(relative)
    if not safe_path(root, ".creator/ARCHITECTURE.md").exists():
        changes.append(".creator/ARCHITECTURE.md")
    return changes


def bootstrap(root: Path, *, workspace_id: str = "creator-workspace", display_name: str = "Creator Workspace", write: bool) -> list[str]:
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    replacements = {"{{timestamp}}": _timestamp(), "{{workspace_id}}": workspace_id, "{{display_name}}": display_name}
    changes = planned_changes(root)
    if not write:
        return changes
    for relative in STATE_FILES:
        destination = safe_path(root, relative)
        if destination.exists():
            load_json(destination)
            continue
        source = _template_path(relative)
        if not source.is_file():
            raise BootstrapError(f"missing workspace template: {source}")
        value = json.loads(source.read_text(encoding="utf-8"))
        atomic_write_json(destination, _render(value, replacements), mode=0o600)
    architecture = safe_path(root, ".creator/ARCHITECTURE.md")
    if not architecture.exists():
        atomic_write_text(architecture, ARCHITECTURE_TEMPLATE, mode=0o600)
    findings = validate_workspace(root)
    if findings:
        raise BootstrapError("; ".join(findings))
    return changes


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--workspace-id", default="creator-workspace")
    parser.add_argument("--display-name", default="Creator Workspace")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.check:
            findings = validate_workspace(args.root)
            if findings:
                for finding in findings:
                    print(f"FAIL: {finding}", file=sys.stderr)
                return 1
            print("Creator workspace validation passed.")
            return 0
        changes = bootstrap(args.root, workspace_id=args.workspace_id, display_name=args.display_name, write=not args.dry_run)
    except (BootstrapError, StateStoreError, OSError, json.JSONDecodeError) as exc:
        print(f"Workspace bootstrap failed: {exc}", file=sys.stderr)
        return 1
    action = "Would create" if args.dry_run else "Created"
    if changes:
        for path in changes:
            print(f"{action}: {path}")
    else:
        print("Workspace already satisfies the bootstrap contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
