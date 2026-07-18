#!/usr/bin/env python3
"""Deterministic execution closure, state-update proposal, and recovery workflows."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_execution_lifecycle import (
        ALLOWED_TRANSITIONS,
        ExecutionLifecycleError,
        RECONCILIATION_SCHEMA,
        ROOT,
        _load_execution,
        _relative_path,
        _require_relative_file,
        _restore,
        _snapshot,
        _validate_document,
        _validate_execution_documents,
        inspect_execution,
    )
    from creator_ids import deterministic_id
    from creator_ledger import append_event, new_event, read_events
    from creator_transactions import atomic_write_json, atomic_write_text
except ImportError:  # Imported as scripts.creator_execution_closure in tests.
    from scripts.creator_execution_lifecycle import (
        ALLOWED_TRANSITIONS,
        ExecutionLifecycleError,
        RECONCILIATION_SCHEMA,
        ROOT,
        _load_execution,
        _relative_path,
        _require_relative_file,
        _restore,
        _snapshot,
        _validate_document,
        _validate_execution_documents,
        inspect_execution,
    )
    from scripts.creator_ids import deterministic_id
    from scripts.creator_ledger import append_event, new_event, read_events
    from scripts.creator_transactions import atomic_write_json, atomic_write_text

STATE_UPDATE_PROPOSAL_SCHEMA = Path("schemas/execution/state-update-proposal.schema.json")
TERMINAL_STATES = {"DONE", "DONE_WITH_CONCERNS"}
RECOVERY_TYPES = {
    "orphan-plan",
    "interrupted-execution",
    "failed-verification",
    "blocked-task",
    "state-divergence",
    "scope-creep",
    "incomplete-reconciliation",
}

RECOVERY_TARGETS = {
    "orphan-plan": {
        "APPROVED": "BLOCKED",
        "EXECUTING": "RECOVERING",
        "VERIFYING": "EXECUTING",
        "RECONCILING": "RECOVERING",
    },
    "interrupted-execution": {"EXECUTING": "RECOVERING"},
    "failed-verification": {"VERIFYING": "EXECUTING"},
    "blocked-task": {"EXECUTING": "RECOVERING", "BLOCKED": "RECOVERING"},
    "state-divergence": {
        "EXECUTING": "RECOVERING",
        "VERIFYING": "EXECUTING",
        "RECONCILING": "RECOVERING",
        "BLOCKED": "RECOVERING",
    },
    "scope-creep": {
        "EXECUTING": "BLOCKED",
        "VERIFYING": "BLOCKED",
        "RECOVERING": "BLOCKED",
    },
    "incomplete-reconciliation": {"RECONCILING": "RECOVERING"},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean_strings(values: list[str] | None, field: str) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
        raise ExecutionLifecycleError(f"{field} must be an array of strings")
    return [item.strip() for item in values if item.strip()]


def _verified_task_records(root: Path, tasks: dict[str, Any]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for task in tasks["tasks"]:
        verification = task["verification"]
        if task["status"] != "VERIFIED" or verification["status"] != "PASS":
            raise ExecutionLifecycleError(
                f"closure requires verified PASS evidence for task {task['task_id']}"
            )
        evidence_relative = verification.get("evidence_path")
        recorded_hash = verification.get("evidence_hash")
        if not isinstance(evidence_relative, str) or not evidence_relative:
            raise ExecutionLifecycleError(
                f"verified task {task['task_id']} is missing evidence_path"
            )
        if not isinstance(recorded_hash, str) or len(recorded_hash) != 64:
            raise ExecutionLifecycleError(
                f"verified task {task['task_id']} is missing a SHA-256 evidence hash"
            )
        evidence_path = _require_relative_file(root, evidence_relative)
        current_hash = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        if current_hash != recorded_hash:
            raise ExecutionLifecycleError(
                f"verification evidence changed after verification: {evidence_relative}"
            )
        records.append(
            {
                "task_id": task["task_id"],
                "evidence_path": evidence_relative,
                "evidence_hash": recorded_hash,
            }
        )
    return records


def _next_closure_sequence(execution_dir: Path) -> int:
    sequences: list[int] = []
    for path in execution_dir.glob("RECONCILIATION-*.json"):
        stem = path.stem
        try:
            sequences.append(int(stem.rsplit("-", 1)[1]))
        except (IndexError, ValueError):
            continue
    return max(sequences, default=0) + 1


def _render_reconciliation_markdown(record: dict[str, Any]) -> str:
    planned = "\n".join(f"- `{item}`" for item in record["planned_tasks"])
    actual = "\n".join(f"- `{item}`" for item in record["actual_tasks"])
    deviations = "\n".join(f"- {item}" for item in record["deviations"]) or "- none"
    concerns = "\n".join(f"- {item}" for item in record["concerns"]) or "- none"
    return f"""# RECONCILIATION-{record['sequence']:03d}

**Project ID:** `{record['project_id']}`  
**Status:** `{record['status']}`  
**Created At:** `{record['created_at']}`

## Planned Tasks

{planned}

## Actual Verified Tasks

{actual}

## Deviations

{deviations}

## Concerns

{concerns}

## State Update Proposal

`{record['state_update_proposal']}`

## Recommended Next Action

{record['recommended_next_action']}
"""


def _render_summary(
    *,
    project_id: str,
    status: str,
    sequence: int,
    verified_tasks: list[dict[str, str]],
    deviations: list[str],
    concerns: list[str],
    proposal_relative: str,
    recommended_next_action: str,
    timestamp: str,
) -> str:
    evidence = "\n".join(
        f"- `{item['task_id']}` → `{item['evidence_path']}` "
        f"(`{item['evidence_hash']}`)"
        for item in verified_tasks
    )
    deviation_text = "\n".join(f"- {item}" for item in deviations) or "- none"
    concern_text = "\n".join(f"- {item}" for item in concerns) or "- none"
    return f"""# SUMMARY-{sequence:03d}

**Project ID:** `{project_id}`  
**Final Status:** `{status}`  
**Closed At:** `{timestamp}`

## Verified Task Evidence

{evidence}

## Deviations

{deviation_text}

## Residual Concerns

{concern_text}

## State Update Boundary

A staged proposal was created at `{proposal_relative}`.  
`creator-execution-cycle` did not apply workspace state directly.

## Recommended Next Action

{recommended_next_action}
"""


def close_execution(
    root: Path,
    project_id: str,
    *,
    status: str,
    actor: str,
    recommended_next_action: str,
    deviations: list[str] | None = None,
    concerns: list[str] | None = None,
    timestamp: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    status = status.upper()
    actor = actor.strip()
    recommended_next_action = recommended_next_action.strip()
    deviations = _clean_strings(deviations, "deviations")
    concerns = _clean_strings(concerns, "concerns")

    if status not in TERMINAL_STATES:
        raise ExecutionLifecycleError("closure status must be DONE or DONE_WITH_CONCERNS")
    if not actor:
        raise ExecutionLifecycleError("actor must be non-empty")
    if not recommended_next_action:
        raise ExecutionLifecycleError("recommended_next_action must be non-empty")
    if status == "DONE" and concerns:
        raise ExecutionLifecycleError("DONE closure cannot contain residual concerns")
    if status == "DONE_WITH_CONCERNS" and not concerns:
        raise ExecutionLifecycleError(
            "DONE_WITH_CONCERNS closure requires at least one concern"
        )

    execution_dir, state, tasks = _load_execution(
        root, project_id, schema_root=schema_root
    )
    if state["current_state"] != "RECONCILING":
        raise ExecutionLifecycleError("closure requires execution state RECONCILING")
    if status not in ALLOWED_TRANSITIONS["RECONCILING"]:
        raise ExecutionLifecycleError(
            f"illegal closure transition: RECONCILING -> {status}"
        )

    verified_tasks = _verified_task_records(root, tasks)
    closure_sequence = _next_closure_sequence(execution_dir)
    suffix = f"{closure_sequence:03d}"
    reconciliation_json_name = f"RECONCILIATION-{suffix}.json"
    reconciliation_md_name = f"RECONCILIATION-{suffix}.md"
    summary_name = f"SUMMARY-{suffix}.md"
    proposal_name = "state-update-proposal.json"

    reconciliation_json_path = execution_dir / reconciliation_json_name
    reconciliation_md_path = execution_dir / reconciliation_md_name
    summary_path = execution_dir / summary_name
    proposal_path = execution_dir / proposal_name
    for path in (
        reconciliation_json_path,
        reconciliation_md_path,
        summary_path,
        proposal_path,
    ):
        if path.exists():
            raise ExecutionLifecycleError(f"closure artifact already exists: {path.name}")

    proposal_relative = _relative_path(root, proposal_path)
    reconciliation_record = {
        "schema_version": "1.0.0",
        "project_id": project_id,
        "sequence": closure_sequence,
        "status": status,
        "planned_tasks": [task["task_id"] for task in tasks["tasks"]],
        "actual_tasks": [item["task_id"] for item in verified_tasks],
        "deviations": deviations,
        "concerns": concerns,
        "state_update_proposal": proposal_relative,
        "recommended_next_action": recommended_next_action,
        "created_at": timestamp,
    }
    proposal = {
        "schema_version": "1.0.0",
        "proposal_id": deterministic_id(
            "PROPOSAL", project_id, closure_sequence, status
        ),
        "operation": "update-project-execution",
        "status": "staged",
        "target_surface": ".creator/projects.json",
        "owner_skill": "creator-workspace-manager",
        "requested_by": "creator-execution-cycle",
        "project_id": project_id,
        "execution_status": status,
        "source_execution": _relative_path(root, execution_dir),
        "reconciliation_record": _relative_path(root, reconciliation_json_path),
        "reconciliation_markdown": _relative_path(root, reconciliation_md_path),
        "summary": _relative_path(root, summary_path),
        "verified_tasks": verified_tasks,
        "concerns": concerns,
        "recommended_next_action": recommended_next_action,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    _validate_document(
        reconciliation_record,
        RECONCILIATION_SCHEMA,
        "reconciliation record",
        schema_root=schema_root,
    )
    _validate_document(
        proposal,
        STATE_UPDATE_PROPOSAL_SCHEMA,
        "state update proposal",
        schema_root=schema_root,
    )

    state_path = execution_dir / "execution-state.json"
    ledger_path = execution_dir / "activity_ledger.jsonl"
    snapshot = _snapshot(
        [
            state_path,
            ledger_path,
            reconciliation_json_path,
            reconciliation_md_path,
            summary_path,
            proposal_path,
        ]
    )
    transition_sequence = state["sequence"] + 1
    state["current_state"] = status
    state["sequence"] = transition_sequence
    state["updated_at"] = timestamp
    state["history"].append(
        {
            "sequence": transition_sequence,
            "from_state": "RECONCILING",
            "to_state": status,
            "actor": actor,
            "reason": "Evidence-backed reconciliation and mandatory closure completed.",
            "ts": timestamp,
        }
    )
    state["artifacts"]["reconciliation"] = reconciliation_json_name
    state["artifacts"]["summary"] = summary_name
    state["artifacts"]["state_update_proposal"] = proposal_name

    try:
        atomic_write_json(
            reconciliation_json_path, reconciliation_record, mode=0o600
        )
        atomic_write_text(
            reconciliation_md_path,
            _render_reconciliation_markdown(reconciliation_record),
            mode=0o600,
        )
        atomic_write_text(
            summary_path,
            _render_summary(
                project_id=project_id,
                status=status,
                sequence=closure_sequence,
                verified_tasks=verified_tasks,
                deviations=deviations,
                concerns=concerns,
                proposal_relative=proposal_relative,
                recommended_next_action=recommended_next_action,
                timestamp=timestamp,
            ),
            mode=0o600,
        )
        atomic_write_json(proposal_path, proposal, mode=0o600)
        atomic_write_json(state_path, state, mode=0o600)
        ledger_sequence = len(read_events(ledger_path)) + 1
        append_event(
            ledger_path,
            new_event(
                event_id=deterministic_id(
                    "EVENT", project_id, "closure", closure_sequence, status
                ),
                sequence=ledger_sequence,
                phase="reconcile",
                task_id=project_id,
                artifact=summary_name,
                status=status,
                evidence_path=_relative_path(root, reconciliation_md_path),
                notes=recommended_next_action,
                ts=timestamp,
            ),
        )
        _validate_execution_documents(execution_dir, schema_root=schema_root)
        _validate_document(
            json.loads(reconciliation_json_path.read_text(encoding="utf-8")),
            RECONCILIATION_SCHEMA,
            "written reconciliation record",
            schema_root=schema_root,
        )
        _validate_document(
            json.loads(proposal_path.read_text(encoding="utf-8")),
            STATE_UPDATE_PROPOSAL_SCHEMA,
            "written state update proposal",
            schema_root=schema_root,
        )
        _verified_task_records(root, tasks)
    except Exception:
        _restore(snapshot)
        raise

    result = inspect_execution(root, project_id, schema_root=schema_root)
    result["closure"] = {
        "status": status,
        "reconciliation_record": _relative_path(root, reconciliation_json_path),
        "reconciliation_markdown": _relative_path(root, reconciliation_md_path),
        "summary": _relative_path(root, summary_path),
        "state_update_proposal": proposal_relative,
        "recommended_next_action": recommended_next_action,
    }
    return result


def _append_recovery_section(
    path: Path,
    *,
    recovery_number: int,
    recovery_type: str,
    project_id: str,
    current_state: str,
    target_state: str,
    actor: str,
    reason: str,
    timestamp: str,
) -> str:
    existing = path.read_text(encoding="utf-8").rstrip() if path.is_file() else ""
    heading = "# Recovery Plan" if not existing else ""
    section = f"""## Recovery {recovery_number}: {recovery_type}

**Project ID:** `{project_id}`  
**From State:** `{current_state}`  
**Target State:** `{target_state}`  
**Actor:** `{actor}`  
**Recorded At:** `{timestamp}`

### Trigger

{reason}

### Guardrails

- Preserve existing verification evidence and ledger history.
- Do not bypass task verification.
- Do not apply workspace state directly.
- Return only through an allowed lifecycle transition.
"""
    return "\n\n".join(part for part in (heading, existing, section) if part) + "\n"


def _recovery_specific_artifacts(recovery_type: str) -> list[str]:
    if recovery_type in {"orphan-plan", "incomplete-reconciliation"}:
        return ["RECONCILIATION-RECOVERY.md"]
    if recovery_type == "state-divergence":
        return ["STATE-DIVERGENCE.md"]
    if recovery_type == "scope-creep":
        return ["SCOPE-CREEP.md", "BLOCKER.md"]
    if recovery_type == "blocked-task":
        return ["BLOCKER.md"]
    return []


def _validate_recovery_preconditions(
    execution_dir: Path,
    state: dict[str, Any],
    tasks: dict[str, Any],
    recovery_type: str,
) -> str:
    current = state["current_state"]
    target = RECOVERY_TARGETS.get(recovery_type, {}).get(current)
    if target is None:
        raise ExecutionLifecycleError(
            f"{recovery_type} recovery is not valid from {current}"
        )
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ExecutionLifecycleError(
            f"recovery would violate lifecycle transition: {current} -> {target}"
        )
    statuses = {task["status"] for task in tasks["tasks"]}
    if recovery_type == "failed-verification" and "FAILED" not in statuses:
        raise ExecutionLifecycleError(
            "failed-verification recovery requires at least one FAILED task"
        )
    if recovery_type == "blocked-task" and current != "BLOCKED" and "BLOCKED" not in statuses:
        raise ExecutionLifecycleError(
            "blocked-task recovery requires a BLOCKED execution or task"
        )
    if recovery_type == "orphan-plan":
        if not (execution_dir / "PLAN-001.md").is_file():
            raise ExecutionLifecycleError("orphan-plan recovery requires PLAN-001.md")
        if state["artifacts"].get("reconciliation") is not None:
            raise ExecutionLifecycleError(
                "orphan-plan recovery requires a missing reconciliation"
            )
    if recovery_type == "incomplete-reconciliation":
        if all(
            isinstance(state["artifacts"].get(key), str)
            for key in ("reconciliation", "summary", "state_update_proposal")
        ):
            raise ExecutionLifecycleError(
                "incomplete-reconciliation recovery requires missing closure artifacts"
            )
    return target


def recover_execution(
    root: Path,
    project_id: str,
    *,
    recovery_type: str,
    actor: str,
    reason: str,
    timestamp: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    recovery_type = recovery_type.strip()
    actor = actor.strip()
    reason = reason.strip()
    if recovery_type not in RECOVERY_TYPES:
        raise ExecutionLifecycleError(f"unknown recovery type: {recovery_type}")
    if not actor or not reason:
        raise ExecutionLifecycleError("actor and reason must be non-empty")

    execution_dir, state, tasks = _load_execution(
        root, project_id, schema_root=schema_root
    )
    current = state["current_state"]
    target = _validate_recovery_preconditions(
        execution_dir, state, tasks, recovery_type
    )
    ledger_path = execution_dir / "activity_ledger.jsonl"
    recovery_path = execution_dir / "RECOVERY-PLAN.md"
    specific_names = _recovery_specific_artifacts(recovery_type)
    if target == "BLOCKED" and "BLOCKER.md" not in specific_names:
        specific_names.append("BLOCKER.md")
    specific_paths = [execution_dir / name for name in specific_names]
    state_path = execution_dir / "execution-state.json"
    snapshot = _snapshot([state_path, ledger_path, recovery_path, *specific_paths])
    recovery_number = (
        sum(1 for event in read_events(ledger_path) if event.get("phase") == "recover")
        + 1
    )

    state["current_state"] = target
    state["sequence"] += 1
    state["updated_at"] = timestamp
    state["history"].append(
        {
            "sequence": state["sequence"],
            "from_state": current,
            "to_state": target,
            "actor": actor,
            "reason": f"{recovery_type}: {reason}",
            "ts": timestamp,
        }
    )
    state["artifacts"]["recovery_plan"] = "RECOVERY-PLAN.md"
    if "BLOCKER.md" in specific_names:
        state["artifacts"]["blocker"] = "BLOCKER.md"

    try:
        atomic_write_text(
            recovery_path,
            _append_recovery_section(
                recovery_path,
                recovery_number=recovery_number,
                recovery_type=recovery_type,
                project_id=project_id,
                current_state=current,
                target_state=target,
                actor=actor,
                reason=reason,
                timestamp=timestamp,
            ),
            mode=0o600,
        )
        for path in specific_paths:
            title = path.stem.replace("-", " ").title()
            existing = path.read_text(encoding="utf-8").rstrip() if path.is_file() else ""
            section = f"""# {title}

**Project ID:** `{project_id}`  
**Recovery Type:** `{recovery_type}`  
**From State:** `{current}`  
**Target State:** `{target}`  
**Recorded At:** `{timestamp}`

## Evidence

{reason}

## Required Resolution

Resume only through the allowed lifecycle and preserve verification and closure gates.
"""
            text = section if not existing else f"{existing}\n\n---\n\n{section}"
            atomic_write_text(path, text, mode=0o600)
        atomic_write_json(state_path, state, mode=0o600)
        ledger_sequence = len(read_events(ledger_path)) + 1
        primary_artifact = specific_names[0] if specific_names else "RECOVERY-PLAN.md"
        append_event(
            ledger_path,
            new_event(
                event_id=deterministic_id(
                    "EVENT",
                    project_id,
                    "recover",
                    recovery_number,
                    recovery_type,
                    target,
                ),
                sequence=ledger_sequence,
                phase="recover",
                task_id=project_id,
                artifact=primary_artifact,
                status=target,
                evidence_path=_relative_path(root, recovery_path),
                notes=f"{recovery_type}: {reason}",
                ts=timestamp,
            ),
        )
        _validate_execution_documents(execution_dir, schema_root=schema_root)
    except Exception:
        _restore(snapshot)
        raise

    result = inspect_execution(root, project_id, schema_root=schema_root)
    result["recovery"] = {
        "type": recovery_type,
        "from_state": current,
        "to_state": target,
        "recovery_plan": _relative_path(root, recovery_path),
        "specific_artifacts": [
            _relative_path(root, path) for path in specific_paths
        ],
    }
    return result


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    close = subparsers.add_parser("close")
    close.add_argument("--root", type=Path, default=Path.cwd())
    close.add_argument("--project-id", required=True)
    close.add_argument(
        "--status", choices=("DONE", "DONE_WITH_CONCERNS"), required=True
    )
    close.add_argument("--actor", required=True)
    close.add_argument("--recommended-next-action", required=True)
    close.add_argument("--deviation", action="append", default=[])
    close.add_argument("--concern", action="append", default=[])

    recover = subparsers.add_parser("recover")
    recover.add_argument("--root", type=Path, default=Path.cwd())
    recover.add_argument("--project-id", required=True)
    recover.add_argument("--type", choices=sorted(RECOVERY_TYPES), required=True)
    recover.add_argument("--actor", required=True)
    recover.add_argument("--reason", required=True)

    status = subparsers.add_parser("status")
    status.add_argument("--root", type=Path, default=Path.cwd())
    status.add_argument("--project-id", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.command == "close":
            result = close_execution(
                args.root,
                args.project_id,
                status=args.status,
                actor=args.actor,
                recommended_next_action=args.recommended_next_action,
                deviations=args.deviation,
                concerns=args.concern,
            )
        elif args.command == "recover":
            result = recover_execution(
                args.root,
                args.project_id,
                recovery_type=args.type,
                actor=args.actor,
                reason=args.reason,
            )
        else:
            result = inspect_execution(args.root, args.project_id)
    except (ExecutionLifecycleError, OSError, json.JSONDecodeError) as exc:
        print(f"Creator Execution Closure failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
