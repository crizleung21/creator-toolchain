#!/usr/bin/env python3
"""Read-only maintenance review and explicitly confirmed non-destructive archive operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from creator_health_check import HEALTH_REPORT_RELATIVE, calculate_health, write_health
    from creator_ids import deterministic_id
    from creator_ledger import append_event, new_event, read_events
    from creator_state_store import STATE_FILES, load_json, safe_path, validate_workspace
    from creator_transactions import atomic_write_bytes, atomic_write_json
    from creator_workspace_proposals import discover_proposals
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:  # Imported as scripts.creator_workspace_maintenance in tests.
    from scripts.creator_health_check import HEALTH_REPORT_RELATIVE, calculate_health, write_health
    from scripts.creator_ids import deterministic_id
    from scripts.creator_ledger import append_event, new_event, read_events
    from scripts.creator_state_store import STATE_FILES, load_json, safe_path, validate_workspace
    from scripts.creator_transactions import atomic_write_bytes, atomic_write_json
    from scripts.creator_workspace_proposals import discover_proposals
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE_ROOT = Path(".creator/maintenance")
ARCHIVE_PROPOSAL_ROOT = MAINTENANCE_ROOT / "archive-proposals"
ARCHIVE_RECEIPT_ROOT = MAINTENANCE_ROOT / "archive-receipts"
ARCHIVE_LEDGER_RELATIVE = MAINTENANCE_ROOT / "activity_ledger.jsonl"
ARCHIVE_ROOT = Path(".creator/archive")
MAINTENANCE_SCHEMA = Path("schemas/workspace/maintenance-report.schema.json")
ARCHIVE_PROPOSAL_SCHEMA = Path("schemas/workspace/archive-proposal.schema.json")
ARCHIVE_RECEIPT_SCHEMA = Path("schemas/workspace/archive-receipt.schema.json")
CONTROL_PREFIXES = (
    ".creator/archive",
    ".creator/maintenance",
    ".creator/health",
    ".creator/reconciliation",
)


class MaintenanceError(RuntimeError):
    """Raised when a maintenance or archive request violates the workspace contract."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _snapshot(paths: Iterable[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.is_file() else None for path in paths}


def _restore(snapshot: dict[Path, bytes | None]) -> None:
    for path, data in snapshot.items():
        if data is None:
            if path.exists():
                path.unlink()
        else:
            atomic_write_bytes(path, data, mode=0o600)


def _iter_json_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_json_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_json_strings(item)


def _path_digest(path: Path) -> str:
    if path.is_symlink():
        raise MaintenanceError(f"archive target cannot be a symbolic link: {path}")
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if not path.is_dir():
        raise MaintenanceError(f"archive target must be a file or directory: {path}")
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*"), key=lambda value: value.relative_to(path).as_posix()):
        if item.is_symlink():
            raise MaintenanceError(f"archive target contains a symbolic link: {item}")
        relative = item.relative_to(path).as_posix()
        if item.is_dir():
            digest.update(f"D\0{relative}\0".encode("utf-8"))
        elif item.is_file():
            digest.update(f"F\0{relative}\0".encode("utf-8"))
            digest.update(hashlib.sha256(item.read_bytes()).digest())
        else:
            raise MaintenanceError(f"archive target contains an unsupported entry: {item}")
    return digest.hexdigest()


def _normalize_archive_target(root: Path, target_relative: str) -> tuple[Path, str]:
    relative = Path(target_relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise MaintenanceError("archive target must be a safe repository-relative path")
    normalized = relative.as_posix()
    if not normalized.startswith(".creator/"):
        raise MaintenanceError("archive target must be inside .creator/")
    if normalized in set(STATE_FILES):
        raise MaintenanceError("root state surfaces cannot be archived")
    if any(normalized == prefix or normalized.startswith(prefix + "/") for prefix in CONTROL_PREFIXES):
        raise MaintenanceError("workspace control, health, reconciliation, and archive paths cannot be archived")
    path = safe_path(root, relative)
    if not path.exists():
        raise MaintenanceError(f"archive target is missing: {normalized}")
    if path.is_symlink():
        raise MaintenanceError("archive target cannot be a symbolic link")
    return path, normalized


def _reference_conflicts(root: Path, target_relative: str) -> list[str]:
    conflicts: list[str] = []
    creator_root = root / ".creator"
    if not creator_root.is_dir():
        return conflicts
    for document in sorted(creator_root.rglob("*.json")):
        relative_document = document.relative_to(root).as_posix()
        if any(relative_document == prefix or relative_document.startswith(prefix + "/") for prefix in CONTROL_PREFIXES):
            continue
        target_path = root / target_relative
        if document.is_relative_to(target_path):
            continue
        try:
            value = json.loads(document.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for reference in _iter_json_strings(value):
            if not reference.startswith(".creator/"):
                continue
            if reference == target_relative or reference.startswith(target_relative.rstrip("/") + "/"):
                conflicts.append(f"{relative_document} references {reference}")
    return sorted(set(conflicts))


def maintenance_review(
    root: Path,
    *,
    generated_at: str | None = None,
    stale_plan_days: int = 30,
    include_repository_checks: bool = True,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    generated_at = generated_at or _now()
    health = calculate_health(
        root,
        calculated_at=generated_at,
        stale_plan_days=stale_plan_days,
        include_repository_checks=include_repository_checks,
        schema_root=schema_root,
    )
    proposals = discover_proposals(root, schema_root=schema_root)
    archive_candidates: list[dict[str, str]] = []
    for signal in health["signals"]:
        if signal["signal_id"] == "STALE_PLAN" and signal["path"].endswith("/project.json"):
            candidate = str(Path(signal["path"]).parent)
            archive_candidates.append({"path": candidate, "reason": signal["message"], "source_signal": signal["signal_id"]})
        elif signal["signal_id"] == "ORPHAN_EXECUTION":
            archive_candidates.append({"path": signal["path"], "reason": signal["message"], "source_signal": signal["signal_id"]})
    state_fixes = [
        {"signal_id": signal["signal_id"], "level": signal["level"], "path": signal["path"], "message": signal["message"]}
        for signal in health["signals"]
    ]
    rule_proposals_root = root / ".creator/rule-proposals"
    rule_proposals = [path.relative_to(root).as_posix() for path in sorted(rule_proposals_root.glob("*.json"))] if rule_proposals_root.is_dir() else []
    report = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "health_level": health["level"],
        "health_score": health["score"],
        "proposal_counts": proposals["counts"],
        "archive_candidates": sorted(archive_candidates, key=lambda item: item["path"]),
        "state_fixes": state_fixes,
        "rule_proposals": rule_proposals,
        "recommended_next_action": health["recommended_next_action"] if health["level"] != "green" else "Review staged proposals; no state or archive mutation is required.",
    }
    findings = validate_json_schema(report, load_schema(schema_root / MAINTENANCE_SCHEMA))
    if findings:
        raise MaintenanceError("maintenance report failed schema validation: " + "; ".join(findings))
    return report


def create_archive_proposal(
    root: Path,
    target_relative: str,
    *,
    actor: str,
    reason: str,
    timestamp: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    if not actor.strip() or not reason.strip():
        raise MaintenanceError("actor and reason must be non-empty")
    target, normalized = _normalize_archive_target(root, target_relative)
    conflicts = _reference_conflicts(root, normalized)
    if conflicts:
        raise MaintenanceError("archive target is still referenced: " + "; ".join(conflicts))
    target_hash = _path_digest(target)
    proposal_id = deterministic_id("ARCHIVE", normalized, target_hash, timestamp)
    destination = (ARCHIVE_ROOT / proposal_id / target.name).as_posix()
    proposal_relative = (ARCHIVE_PROPOSAL_ROOT / f"{proposal_id}.json").as_posix()
    proposal_path = safe_path(root, proposal_relative)
    ledger_path = safe_path(root, ARCHIVE_LEDGER_RELATIVE)
    if proposal_path.exists():
        raise MaintenanceError(f"archive proposal already exists: {proposal_relative}")
    proposal = {
        "schema_version": "1.0.0",
        "proposal_id": proposal_id,
        "operation": "archive",
        "status": "staged",
        "target_path": normalized,
        "target_kind": "directory" if target.is_dir() else "file",
        "target_sha256": target_hash,
        "destination_path": destination,
        "requested_by": actor.strip(),
        "reason": reason.strip(),
        "created_at": timestamp,
        "proposal_path": proposal_relative,
    }
    findings = validate_json_schema(proposal, load_schema(schema_root / ARCHIVE_PROPOSAL_SCHEMA))
    if findings:
        raise MaintenanceError("archive proposal failed schema validation: " + "; ".join(findings))
    snapshot = _snapshot([proposal_path, ledger_path])
    try:
        atomic_write_json(proposal_path, proposal, mode=0o600)
        append_event(
            ledger_path,
            new_event(
                event_id=f"EVENT-{hashlib.sha256((proposal_id + ':planned').encode()).hexdigest().upper()[:12]}",
                sequence=len(read_events(ledger_path)) + 1,
                phase="maintenance",
                task_id=proposal_id,
                artifact=proposal_relative,
                status="PLANNED",
                evidence_path=normalized,
                notes=f"{actor.strip()} staged a non-destructive archive proposal: {reason.strip()}",
                ts=timestamp,
            ),
        )
    except Exception:
        _restore(snapshot)
        raise
    return proposal


def archive_status(root: Path, proposal_relative: str, *, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    proposal_path = safe_path(root, proposal_relative)
    if not proposal_path.is_file():
        raise MaintenanceError(f"archive proposal is missing: {proposal_relative}")
    proposal = load_json(proposal_path)
    findings = validate_json_schema(proposal, load_schema(schema_root / ARCHIVE_PROPOSAL_SCHEMA))
    if findings:
        raise MaintenanceError("archive proposal failed schema validation: " + "; ".join(findings))
    receipt_relative = (ARCHIVE_RECEIPT_ROOT / f"{proposal['proposal_id']}.json").as_posix()
    receipt_path = safe_path(root, receipt_relative)
    lifecycle_status = "staged"
    if receipt_path.is_file():
        receipt = load_json(receipt_path)
        receipt_findings = validate_json_schema(receipt, load_schema(schema_root / ARCHIVE_RECEIPT_SCHEMA))
        if receipt_findings:
            raise MaintenanceError("archive receipt failed schema validation: " + "; ".join(receipt_findings))
        lifecycle_status = "archived"
    return {**proposal, "lifecycle_status": lifecycle_status, "receipt_path": receipt_relative if receipt_path.is_file() else None}


def apply_archive(
    root: Path,
    proposal_relative: str,
    *,
    actor: str,
    confirm: str,
    timestamp: str | None = None,
    schema_root: Path = ROOT,
    include_repository_checks: bool = True,
    fail_after_move: bool = False,
) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    if not actor.strip():
        raise MaintenanceError("actor must be non-empty")
    status = archive_status(root, proposal_relative, schema_root=schema_root)
    if status["lifecycle_status"] != "staged":
        raise MaintenanceError("archive proposal is no longer staged")
    proposal_id = status["proposal_id"]
    if confirm != proposal_id:
        raise MaintenanceError(f"archive apply requires exact confirmation token: {proposal_id}")
    source, normalized = _normalize_archive_target(root, status["target_path"])
    conflicts = _reference_conflicts(root, normalized)
    if conflicts:
        raise MaintenanceError("archive target is still referenced: " + "; ".join(conflicts))
    if _path_digest(source) != status["target_sha256"]:
        raise MaintenanceError("archive target changed after proposal creation")
    destination = safe_path(root, status["destination_path"])
    if destination.exists():
        raise MaintenanceError(f"archive destination already exists: {status['destination_path']}")
    receipt_relative = (ARCHIVE_RECEIPT_ROOT / f"{proposal_id}.json").as_posix()
    receipt_path = safe_path(root, receipt_relative)
    ledger_path = safe_path(root, ARCHIVE_LEDGER_RELATIVE)
    state_path = safe_path(root, ".creator/state.json")
    health_path = safe_path(root, HEALTH_REPORT_RELATIVE)
    snapshot = _snapshot([receipt_path, ledger_path, state_path, health_path])
    receipt = {
        "schema_version": "1.0.0",
        "proposal_id": proposal_id,
        "operation": "archive",
        "status": "archived",
        "source_path": normalized,
        "archive_path": status["destination_path"],
        "source_sha256": status["target_sha256"],
        "archived_by": actor.strip(),
        "archived_at": timestamp,
        "proposal_path": proposal_relative,
        "receipt_path": receipt_relative,
        "health_report": HEALTH_REPORT_RELATIVE.as_posix(),
    }
    receipt_findings = validate_json_schema(receipt, load_schema(schema_root / ARCHIVE_RECEIPT_SCHEMA))
    if receipt_findings:
        raise MaintenanceError("archive receipt failed schema validation: " + "; ".join(receipt_findings))
    moved = False
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, destination)
        moved = True
        if fail_after_move:
            raise MaintenanceError("injected failure after archive move")
        if _path_digest(destination) != status["target_sha256"]:
            raise MaintenanceError("archive checksum mismatch after move")
        atomic_write_json(receipt_path, receipt, mode=0o600)
        append_event(
            ledger_path,
            new_event(
                event_id=f"EVENT-{hashlib.sha256((proposal_id + ':archived:' + timestamp).encode()).hexdigest().upper()[:12]}",
                sequence=len(read_events(ledger_path)) + 1,
                phase="maintenance",
                task_id=proposal_id,
                artifact=receipt_relative,
                status="ARCHIVED",
                evidence_path=proposal_relative,
                notes=f"{actor.strip()} archived {normalized} without deletion.",
                ts=timestamp,
            ),
        )
        health = calculate_health(root, calculated_at=timestamp, include_repository_checks=include_repository_checks, schema_root=schema_root)
        write_health(root, health, schema_root=schema_root)
        findings = validate_workspace(root, schema_root=schema_root)
        if findings:
            raise MaintenanceError("post-archive workspace validation failed: " + "; ".join(findings))
    except Exception:
        if moved and destination.exists() and not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            os.replace(destination, source)
        _restore(snapshot)
        try:
            if destination.parent.is_dir() and not any(destination.parent.iterdir()):
                destination.parent.rmdir()
        except OSError:
            pass
        raise
    return {**receipt, "health": health}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    review = subparsers.add_parser("review")
    review.add_argument("--root", type=Path, default=Path.cwd())
    review.add_argument("--generated-at")
    review.add_argument("--stale-plan-days", type=int, default=30)
    plan = subparsers.add_parser("archive-plan")
    plan.add_argument("--root", type=Path, default=Path.cwd())
    plan.add_argument("--target", required=True)
    plan.add_argument("--actor", required=True)
    plan.add_argument("--reason", required=True)
    plan.add_argument("--timestamp")
    status = subparsers.add_parser("archive-status")
    status.add_argument("--root", type=Path, default=Path.cwd())
    status.add_argument("--proposal", required=True)
    apply = subparsers.add_parser("archive-apply")
    apply.add_argument("--root", type=Path, default=Path.cwd())
    apply.add_argument("--proposal", required=True)
    apply.add_argument("--actor", required=True)
    apply.add_argument("--confirm", required=True)
    apply.add_argument("--timestamp")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.command == "review":
            result = maintenance_review(args.root, generated_at=args.generated_at, stale_plan_days=args.stale_plan_days)
        elif args.command == "archive-plan":
            result = create_archive_proposal(args.root, args.target, actor=args.actor, reason=args.reason, timestamp=args.timestamp)
        elif args.command == "archive-status":
            result = archive_status(args.root, args.proposal)
        else:
            result = apply_archive(args.root, args.proposal, actor=args.actor, confirm=args.confirm, timestamp=args.timestamp)
    except (MaintenanceError, OSError, ValueError) as exc:
        print(f"Creator workspace maintenance failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
