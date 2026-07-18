#!/usr/bin/env python3
"""Discover and inspect immutable Creator Toolchain state proposals."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from creator_state_store import load_json, safe_path
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:  # Imported as scripts.creator_workspace_proposals in tests.
    from scripts.creator_state_store import load_json, safe_path
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
RECONCILIATION_ROOT = Path(".creator/reconciliation")
RECEIPT_SCHEMA = Path("schemas/workspace/reconciliation-receipt.schema.json")
PROPOSAL_SCHEMAS = {
    "register-project": Path("schemas/project/state-registration-proposal.schema.json"),
    "update-project-execution": Path("schemas/execution/state-update-proposal.schema.json"),
}


class ProposalLifecycleError(RuntimeError):
    """Raised when proposal lifecycle evidence is missing or inconsistent."""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _proposal_paths(root: Path) -> list[Path]:
    paths: set[Path] = set()
    state_root = root / ".creator/state-proposals"
    if state_root.is_dir():
        paths.update(path for path in state_root.glob("*.json") if path.is_file())
    execution_root = root / ".creator/executions"
    if execution_root.is_dir():
        paths.update(path for path in execution_root.glob("*/state-update-proposal.json") if path.is_file())
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def _load_valid_proposal(root: Path, proposal_relative: str, *, schema_root: Path) -> tuple[Path, dict[str, Any]]:
    path = safe_path(root, proposal_relative)
    if not path.is_file():
        raise ProposalLifecycleError(f"proposal is missing: {proposal_relative}")
    proposal = load_json(path)
    operation = proposal.get("operation")
    schema_relative = PROPOSAL_SCHEMAS.get(operation)
    if schema_relative is None:
        raise ProposalLifecycleError(f"unsupported proposal operation: {operation!r}")
    findings = validate_json_schema(proposal, load_schema(schema_root / schema_relative))
    if findings:
        raise ProposalLifecycleError("proposal failed schema validation: " + "; ".join(findings))
    if proposal.get("owner_skill") != "creator-workspace-manager":
        raise ProposalLifecycleError("proposal owner must be creator-workspace-manager")
    if proposal.get("target_surface") != ".creator/projects.json":
        raise ProposalLifecycleError("proposal target must be .creator/projects.json")
    if proposal.get("status") != "staged":
        raise ProposalLifecycleError("proposal evidence must remain staged and immutable")
    return path, proposal


def _project_id(proposal: dict[str, Any]) -> str:
    if proposal.get("operation") == "register-project":
        project = proposal.get("project")
        if isinstance(project, dict) and isinstance(project.get("project_id"), str):
            return project["project_id"]
    value = proposal.get("project_id")
    if isinstance(value, str):
        return value
    raise ProposalLifecycleError("proposal has no project_id")


def _lifecycle_record(root: Path, proposal_path: Path, proposal: dict[str, Any], *, schema_root: Path) -> dict[str, Any]:
    proposal_id = proposal["proposal_id"]
    receipt_path = safe_path(root, RECONCILIATION_ROOT / f"{proposal_id}.json")
    lifecycle_status = "staged"
    lifecycle_evidence: str | None = None
    if receipt_path.is_file():
        receipt = load_json(receipt_path)
        findings = validate_json_schema(receipt, load_schema(schema_root / RECEIPT_SCHEMA))
        if findings:
            raise ProposalLifecycleError("reconciliation receipt failed schema validation: " + "; ".join(findings))
        if receipt.get("proposal_id") != proposal_id or receipt.get("proposal_path") != proposal_path.relative_to(root).as_posix():
            raise ProposalLifecycleError(f"receipt does not match proposal: {proposal_id}")
        lifecycle_status = "applied"
        lifecycle_evidence = receipt_path.relative_to(root).as_posix()
    return {
        "proposal_id": proposal_id,
        "operation": proposal["operation"],
        "project_id": _project_id(proposal),
        "requested_by": proposal["requested_by"],
        "owner_skill": proposal["owner_skill"],
        "target_surface": proposal["target_surface"],
        "proposal_path": proposal_path.relative_to(root).as_posix(),
        "proposal_sha256": _sha(proposal_path),
        "lifecycle_status": lifecycle_status,
        "lifecycle_evidence": lifecycle_evidence,
    }


def discover_proposals(root: Path, *, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    records: list[dict[str, Any]] = []
    for path in _proposal_paths(root):
        relative = path.relative_to(root).as_posix()
        try:
            _, proposal = _load_valid_proposal(root, relative, schema_root=schema_root)
            record = _lifecycle_record(root, path, proposal, schema_root=schema_root)
        except (ProposalLifecycleError, OSError, ValueError) as exc:
            record = {
                "proposal_id": "",
                "operation": "",
                "project_id": "",
                "requested_by": "",
                "owner_skill": "",
                "target_surface": "",
                "proposal_path": relative,
                "proposal_sha256": _sha(path),
                "lifecycle_status": "invalid",
                "lifecycle_evidence": None,
                "finding": str(exc),
            }
        records.append(record)

    by_id: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        proposal_id = record.get("proposal_id")
        if isinstance(proposal_id, str) and proposal_id:
            by_id.setdefault(proposal_id, []).append(record)
    for proposal_id, duplicates in by_id.items():
        if len(duplicates) > 1:
            for record in duplicates:
                record["lifecycle_status"] = "invalid"
                record["finding"] = f"duplicate proposal_id across proposal files: {proposal_id}"
                record["lifecycle_evidence"] = None

    records.sort(key=lambda item: item["proposal_path"])
    counts = {status: sum(record["lifecycle_status"] == status for record in records) for status in ("staged", "applied", "invalid")}
    return {
        "schema_version": "1.0.0",
        "proposal_count": len(records),
        "counts": counts,
        "proposals": records,
    }


def proposal_status(root: Path, proposal_relative: str, *, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    relative = safe_path(root, proposal_relative).relative_to(root).as_posix()
    catalog = discover_proposals(root, schema_root=schema_root)
    matches = [record for record in catalog["proposals"] if record["proposal_path"] == relative]
    if not matches:
        raise ProposalLifecycleError(f"proposal is not discoverable: {relative}")
    return matches[0]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    listing = subparsers.add_parser("list")
    listing.add_argument("--root", type=Path, default=Path.cwd())
    status = subparsers.add_parser("status")
    status.add_argument("--root", type=Path, default=Path.cwd())
    status.add_argument("--proposal", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = discover_proposals(args.root) if args.command == "list" else proposal_status(args.root, args.proposal)
    except (ProposalLifecycleError, OSError, ValueError) as exc:
        print(f"Creator proposal lifecycle failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
