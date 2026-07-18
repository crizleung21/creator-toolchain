#!/usr/bin/env python3
"""Preview and atomically apply Creator Toolchain workspace state proposals."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_health_check import HEALTH_REPORT_RELATIVE, calculate_health, write_health
    from creator_ledger import append_event, new_event
    from creator_state_store import StateStoreError, load_json, safe_path, surface_sha256, validate_surface, validate_workspace, write_surface
    from creator_transactions import atomic_write_bytes, atomic_write_json
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:
    from scripts.creator_health_check import HEALTH_REPORT_RELATIVE, calculate_health, write_health
    from scripts.creator_ledger import append_event, new_event
    from scripts.creator_state_store import StateStoreError, load_json, safe_path, surface_sha256, validate_surface, validate_workspace, write_surface
    from scripts.creator_transactions import atomic_write_bytes, atomic_write_json
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_RELATIVE = ".creator/projects.json"
LEDGER_RELATIVE = ".creator/reconciliation/activity_ledger.jsonl"
RECEIPT_SCHEMA = Path("schemas/workspace/reconciliation-receipt.schema.json")
PROPOSAL_SCHEMAS = {
    "register-project": Path("schemas/project/state-registration-proposal.schema.json"),
    "update-project-execution": Path("schemas/execution/state-update-proposal.schema.json"),
}


class ReconciliationError(RuntimeError):
    """Raised when a proposal cannot be safely previewed or applied."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _load_proposal(root: Path, proposal_relative: str, *, schema_root: Path) -> tuple[Path, dict[str, Any]]:
    path = safe_path(root, proposal_relative)
    if not path.is_file():
        raise ReconciliationError(f"proposal is missing: {proposal_relative}")
    proposal = load_json(path)
    operation = proposal.get("operation")
    schema_relative = PROPOSAL_SCHEMAS.get(operation)
    if schema_relative is None:
        raise ReconciliationError(f"unsupported proposal operation: {operation!r}")
    findings = validate_json_schema(proposal, load_schema(schema_root / schema_relative))
    if findings:
        raise ReconciliationError("proposal failed schema validation: " + "; ".join(findings))
    if proposal.get("status") != "staged":
        raise ReconciliationError("only staged proposals can be reconciled")
    if proposal.get("target_surface") != PROJECTS_RELATIVE:
        raise ReconciliationError(f"proposal target must be {PROJECTS_RELATIVE}")
    if proposal.get("owner_skill") != "creator-workspace-manager":
        raise ReconciliationError("proposal owner must be creator-workspace-manager")
    return path, proposal


def _require_evidence(root: Path, proposal: dict[str, Any]) -> None:
    paths: list[str] = []
    if proposal["operation"] == "register-project":
        paths.extend(item for item in proposal.get("evidence_paths", []) if isinstance(item, str))
        paths.append(proposal["source_plan"])
    else:
        paths.extend([proposal["reconciliation_record"], proposal["reconciliation_markdown"], proposal["summary"]])
        for task in proposal.get("verified_tasks", []):
            if isinstance(task, dict) and isinstance(task.get("evidence_path"), str):
                paths.append(task["evidence_path"])
    for relative in sorted(set(paths)):
        path = safe_path(root, relative)
        if not path.is_file():
            raise ReconciliationError(f"proposal evidence is missing: {relative}")


def _candidate_projects(current: dict[str, Any], proposal: dict[str, Any], timestamp: str) -> tuple[dict[str, Any], str]:
    candidate = json.loads(json.dumps(current))
    projects = candidate.get("projects")
    if not isinstance(projects, list):
        raise ReconciliationError("projects surface projects must be an array")
    if proposal["operation"] == "register-project":
        project = json.loads(json.dumps(proposal["project"]))
        project_id = project["project_id"]
        if any(isinstance(item, dict) and item.get("project_id") == project_id for item in projects):
            raise ReconciliationError(f"project is already registered: {project_id}")
        projects.append(project)
        action = "add"
    else:
        project_id = proposal["project_id"]
        project = next((item for item in projects if isinstance(item, dict) and item.get("project_id") == project_id), None)
        if project is None:
            raise ReconciliationError(f"execution update requires a registered project: {project_id}")
        project["status"] = "done"
        project["last_summary"] = proposal["summary"]
        project["updated_at"] = timestamp
        action = "update"
    candidate["updated_at"] = timestamp
    return candidate, action


def preview_reconciliation(root: Path, proposal_relative: str, *, timestamp: str | None = None, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    proposal_path, proposal = _load_proposal(root, proposal_relative, schema_root=schema_root)
    _require_evidence(root, proposal)
    projects_path = safe_path(root, PROJECTS_RELATIVE)
    current = load_json(projects_path)
    candidate, action = _candidate_projects(current, proposal, timestamp)
    findings = validate_surface(PROJECTS_RELATIVE, candidate, schema_root=schema_root)
    if findings:
        raise ReconciliationError("candidate projects surface failed validation: " + "; ".join(findings))
    before = projects_path.read_bytes()
    after = _json_bytes(candidate)
    proposal_id = proposal["proposal_id"]
    return {
        "schema_version": "1.0.0",
        "proposal_id": proposal_id,
        "operation": proposal["operation"],
        "project_id": proposal["project"]["project_id"] if proposal["operation"] == "register-project" else proposal["project_id"],
        "action": action,
        "target_surface": PROJECTS_RELATIVE,
        "proposal_path": proposal_path.relative_to(root).as_posix(),
        "receipt_path": f".creator/reconciliation/{proposal_id}.json",
        "before_sha256": _sha_bytes(before),
        "after_sha256": _sha_bytes(after),
        "changed": before != after,
        "candidate": candidate,
    }


def _snapshot(paths: list[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.is_file() else None for path in paths}


def _restore(snapshot: dict[Path, bytes | None]) -> None:
    for path, data in snapshot.items():
        if data is None:
            if path.exists():
                path.unlink()
        else:
            atomic_write_bytes(path, data, mode=0o600)


def apply_reconciliation(root: Path, proposal_relative: str, *, actor: str, timestamp: str | None = None, schema_root: Path = ROOT, include_repository_checks: bool = True, fail_after_projects: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    if not actor.strip():
        raise ReconciliationError("actor must be non-empty")
    preview = preview_reconciliation(root, proposal_relative, timestamp=timestamp, schema_root=schema_root)
    receipt_path = safe_path(root, preview["receipt_path"])
    if receipt_path.exists():
        raise ReconciliationError(f"proposal already has an applied receipt: {preview['receipt_path']}")
    projects_path = safe_path(root, PROJECTS_RELATIVE)
    state_path = safe_path(root, ".creator/state.json")
    health_path = safe_path(root, HEALTH_REPORT_RELATIVE)
    ledger_path = safe_path(root, LEDGER_RELATIVE)
    snapshot = _snapshot([projects_path, state_path, health_path, ledger_path, receipt_path])
    receipt = {
        "schema_version": "1.0.0",
        "proposal_id": preview["proposal_id"],
        "operation": preview["operation"],
        "status": "applied",
        "target_surface": PROJECTS_RELATIVE,
        "project_id": preview["project_id"],
        "before_sha256": preview["before_sha256"],
        "after_sha256": preview["after_sha256"],
        "applied_by": actor.strip(),
        "applied_at": timestamp,
        "proposal_path": preview["proposal_path"],
        "receipt_path": preview["receipt_path"],
        "health_report": HEALTH_REPORT_RELATIVE.as_posix(),
    }
    receipt_findings = validate_json_schema(receipt, load_schema(schema_root / RECEIPT_SCHEMA))
    if receipt_findings:
        raise ReconciliationError("receipt failed schema validation: " + "; ".join(receipt_findings))
    try:
        write_surface(root, PROJECTS_RELATIVE, preview["candidate"], expected_sha256=preview["before_sha256"], schema_root=schema_root)
        if fail_after_projects:
            raise ReconciliationError("injected failure after projects write")
        atomic_write_json(receipt_path, receipt, mode=0o600)
        current_events = sum(1 for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()) if ledger_path.is_file() else 0
        append_event(
            ledger_path,
            new_event(
                event_id=f"EVENT-{hashlib.sha256((preview['proposal_id'] + timestamp).encode()).hexdigest().upper()[:12]}",
                sequence=current_events + 1,
                phase="reconcile",
                task_id=preview["proposal_id"],
                artifact=preview["receipt_path"],
                status="DONE",
                evidence_path=preview["proposal_path"],
                notes=f"{actor.strip()} applied {preview['operation']} to {PROJECTS_RELATIVE}.",
                ts=timestamp,
            ),
        )
        health = calculate_health(root, calculated_at=timestamp, include_repository_checks=include_repository_checks, schema_root=schema_root)
        write_health(root, health, schema_root=schema_root)
        findings = validate_workspace(root, schema_root=schema_root)
        if findings:
            raise ReconciliationError("post-apply workspace validation failed: " + "; ".join(findings))
        if surface_sha256(projects_path) != preview["after_sha256"]:
            raise ReconciliationError("post-apply projects checksum mismatch")
    except Exception:
        _restore(snapshot)
        raise
    return {**preview, "status": "applied", "applied_by": actor.strip(), "applied_at": timestamp, "health": health}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("preview", "apply"):
        child = subparsers.add_parser(command)
        child.add_argument("--root", type=Path, default=Path.cwd())
        child.add_argument("--proposal", required=True)
        child.add_argument("--timestamp")
        if command == "apply":
            child.add_argument("--actor", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = preview_reconciliation(args.root, args.proposal, timestamp=args.timestamp) if args.command == "preview" else apply_reconciliation(args.root, args.proposal, actor=args.actor, timestamp=args.timestamp)
    except (ReconciliationError, StateStoreError, OSError, ValueError) as exc:
        print(f"Creator state reconciliation failed: {exc}", file=sys.stderr)
        return 2
    output = dict(result)
    output.pop("candidate", None)
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
