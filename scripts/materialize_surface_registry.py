#!/usr/bin/env python3
"""Materialize state registry surfaces and documentation from one canonical config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from creator_surface_registry import load_registry_document, load_surface_registry
    from creator_transactions import atomic_write_text
except ImportError:
    from scripts.creator_surface_registry import load_registry_document, load_surface_registry
    from scripts.creator_transactions import atomic_write_text

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = Path(".creator/surfaces.json")
TEMPLATE_PATH = Path("templates/workspace/surfaces.json")
DOC_PATH = Path("docs/architecture/state-surfaces.md")


def _json_text(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def render_outputs(root: Path = ROOT) -> dict[Path, str]:
    root = Path(root).resolve()
    document = load_registry_document(root)
    surfaces = list(load_surface_registry(root).values())
    state = {
        "created_at": document["created_at"],
        "owner_skill": "creator-workspace-manager",
        "privacy_class": "publishable_template",
        "schema_version": document["state_schema_version"],
        "surfaces": surfaces,
        "updated_at": document["updated_at"],
    }
    template = {
        "schema_version": document["state_schema_version"],
        "owner_skill": "creator-workspace-manager",
        "privacy_class": "publishable_template",
        "created_at": "{{timestamp}}",
        "updated_at": "{{timestamp}}",
        "surfaces": surfaces,
    }
    rows = [
        "# Creator Workspace State Surfaces",
        "",
        "Generated from `config/surface-registry.json`. Do not maintain a second manual registry.",
        "",
        "| Surface ID | Path | Schema | Owner | Privacy | Required | Mutable | Archive |",
        "|---|---|---|---|---|---:|---:|---|",
    ]
    for item in surfaces:
        required = "yes" if item["required"] else "no"
        mutable = "yes" if item["mutable"] else "no"
        rows.append(f"| `{item['surface_id']}` | `{item['path']}` | `{item['schema']}` | `{item['owner_skill']}` | `{item['privacy_class']}` | {required} | {mutable} | `{item['archive_policy']}` |")
    rows.extend([
        "",
        "## Ownership",
        "",
        "- `creator-workspace-manager` owns nine workspace surfaces.",
        "- `creator-rule-router` owns `.creator/rules.json`.",
        "- State changes must be validated, atomic, and evidence-backed.",
        "",
    ])
    return {STATE_PATH: _json_text(state), TEMPLATE_PATH: _json_text(template), DOC_PATH: "\n".join(rows)}


def synchronize(root: Path = ROOT, *, write: bool) -> list[str]:
    root = Path(root).resolve()
    findings: list[str] = []
    for relative, expected in render_outputs(root).items():
        path = root / relative
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual == expected:
            continue
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(path, expected, mode=0o600 if relative.parts[0] == ".creator" else 0o644)
        else:
            findings.append(f"stale surface registry output: {relative.as_posix()}")
    return findings


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        findings = synchronize(args.root, write=args.write)
    except (OSError, ValueError) as exc:
        print(f"Surface registry materialization failed: {exc}", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        return 1
    print("Materialized canonical surface registry." if args.write else "Validated canonical surface registry outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
