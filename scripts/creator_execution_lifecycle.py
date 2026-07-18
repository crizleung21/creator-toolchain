#!/usr/bin/env python3
"""Deterministic execution lifecycle, task state, and verification evidence support."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_ids import deterministic_id
    from creator_ledger import append_event, new_event, read_events
    from creator_state_store import safe_path
    from creator_transactions import atomic_write_bytes, atomic_write_json, atomic_write_text
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:  # Imported as scripts.creator_execution_lifecycle in tests.
    from scripts.creator_ids import deterministic_id
    from scripts.creator_ledger import append_event, new_event, read_events
    from scripts.creator_state_store import safe_path
    from scripts.creator_transactions import atomic_write_bytes, atomic_write_json, atomic_write_text
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
EXECUTION_ROOT = Path(".creator/executions")
HANDOFF_SCHEMA = Path("schemas/project/execution-handoff.schema.json")
EXECUTION_STATE_SCHEMA = Path("schemas/execution/execution-state.schema.json")
TASK_SCHEMA = Path("schemas/execution/task.schema.json")
RECONCILIATION_SCHEMA = Path("schemas/execution/reconciliation.schema.json")

EXECUTION_STATES = {
    "PLANNED",
    "APPROVED",
    "EXECUTING",
    "VERIFYING",
    "RECONCILING",
    "DONE",
    "DONE_WITH_CONCERNS",
    "NEEDS_CONTEXT",
    "BLOCKED",
    "RECOVERING",
}

ALLOWED_TRANSITIONS = {
    "PLANNED": {"APPROVED", "NEEDS_CONTEXT"},
    "APPROVED": {"EXECUTING", "BLOCKED"},
    "EXECUTING": {"VERIFYING", "BLOCKED", "RECOVERING"},
    "VERIFYING": {"EXECUTING", "RECONCILING", "DONE_WITH_CONCERNS", "BLOCKED"},
    "RECONCILING": {"DONE", "DONE_WITH_CONCERNS", "RECOVERING"},
    "BLOCKED": {"RECOVERING", "NEEDS_CONTEXT"},
    "RECOVERING": {"EXECUTING", "VERIFYING", "RECONCILING", "BLOCKED"},
    "DONE": set(),
    "DONE_WITH_CONCERNS": set(),
    "NEEDS_CONTEXT": set(),
}

TASK_TRANSITIONS = {
    "PLANNED": {"EXECUTING", "BLOCKED"},
    "EXECUTING": {"EXECUTED", "BLOCKED"},
    "EXECUTED": set(),
    "VERIFIED": set(),
    "FAILED": {"EXECUTING", "BLOCKED"},
    "BLOCKED": {"EXECUTING"},
}


class ExecutionLifecycleError(RuntimeError):
    """Raised when an execution lifecycle operation would violate a contract."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExecutionLifecycleError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExecutionLifecycleError(f"JSON root must be an object: {path}")
    return value


def _schema_findings(value: dict[str, Any], schema_path: Path, *, schema_root: Path) -> list[str]:
    schema = load_schema(Path(schema_root) / schema_path)
    return validate_json_schema(value, schema)


def _validate_document(value: dict[str, Any], schema_path: Path, label: str, *, schema_root: Path) -> None:
    findings = _schema_findings(value, schema_path, schema_root=schema_root)
    if findings:
        raise ExecutionLifecycleError(f"{label} failed schema validation: {'; '.join(findings)}")


def _relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ExecutionLifecycleError(f"path escapes workspace: {path}") from exc


def _require_relative_file(root: Path, relative: str) -> Path:
    path = safe_path(root, relative)
    if not path.is_file():
        raise ExecutionLifecycleError(f"required file is missing: {relative}")
    return path


def _execution_dir(root: Path, project_id: str) -> Path:
    if not project_id.startswith("PROJECT-"):
        raise ExecutionLifecycleError(f"invalid project_id: {project_id}")
    return safe_path(root, EXECUTION_ROOT / project_id)


def _validate_handoff(root: Path, handoff_relative: str, *, schema_root: Path) -> tuple[Path, dict[str, Any]]:
    if Path(handoff_relative).is_absolute() or ".." in Path(handoff_relative).parts:
        raise ExecutionLifecycleError("handoff path must be repository-relative")
    path = _require_relative_file(root, handoff_relative)
    handoff = _load_json(path)
    _validate_document(handoff, HANDOFF_SCHEMA, "execution handoff", schema_root=schema_root)
    if handoff.get("approval_status") != "approved" or handoff.get("approval_decision") != "handoff-to-execution":
        raise ExecutionLifecycleError("execution requires an explicitly approved handoff-to-execution")
    _require_relative_file(root, handoff["source_plan"])
    for artifact in handoff.get("artifact_paths", []):
        if not isinstance(artifact, str):
            raise ExecutionLifecycleError("handoff artifact path must be a string")
        _require_relative_file(root, artifact)
    expected = f".creator/handoffs/{handoff['project_id']}.json"
    if handoff_relative != expected:
        raise ExecutionLifecycleError(f"handoff path must be {expected}")
    return path, handoff


def _normalize_tasks(raw_tasks: list[dict[str, Any]], project_id: str, timestamp: str) -> dict[str, Any]:
    if not raw_tasks:
        raise ExecutionLifecycleError("at least one execution task is required")
    tasks: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, raw in enumerate(raw_tasks, start=1):
        if not isinstance(raw, dict):
            raise ExecutionLifecycleError(f"task {index} must be an object")
        title = raw.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ExecutionLifecycleError(f"task {index} title must be non-empty")
        criteria = raw.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria or not all(isinstance(item, str) and item.strip() for item in criteria):
            raise ExecutionLifecycleError(f"task {index} acceptance_criteria must be a non-empty string array")
        affected = raw.get("affected_files", [])
        if not isinstance(affected, list) or not all(isinstance(item, str) and item.strip() for item in affected):
            raise ExecutionLifecycleError(f"task {index} affected_files must be a string array")
        for relative in affected:
            candidate = Path(relative)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise ExecutionLifecycleError(f"task {index} has unsafe affected file: {relative}")
        verification = raw.get("verification")
        if not isinstance(verification, dict):
            raise ExecutionLifecycleError(f"task {index} verification must be an object")
        method = verification.get("method")
        expected_result = verification.get("expected_result")
        command = verification.get("command")
        if not isinstance(method, str) or not method.strip():
            raise ExecutionLifecycleError(f"task {index} verification.method must be non-empty")
        if command is not None and not isinstance(command, str):
            raise ExecutionLifecycleError(f"task {index} verification.command must be a string or null")
        if not isinstance(expected_result, str) or not expected_result.strip():
            raise ExecutionLifecycleError(f"task {index} verification.expected_result must be non-empty")
        task_id = deterministic_id("TASK", project_id, index, title.strip())
        if task_id in ids:
            raise ExecutionLifecycleError(f"duplicate task_id: {task_id}")
        ids.add(task_id)
        tasks.append(
            {
                "task_id": task_id,
                "title": title.strip(),
                "status": "PLANNED",
                "acceptance_criteria": [item.strip() for item in criteria],
                "affected_files": [item.strip() for item in affected],
                "verification": {
                    "method": method.strip(),
                    "command": command.strip() if isinstance(command, str) and command.strip() else None,
                    "expected_result": expected_result.strip(),
                    "actual_result": None,
                    "evidence_path": None,
                    "evidence_hash": None,
                    "status": "NOT_RUN",
                    "verified_at": None,
                },
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )
    return {"schema_version": "1.0.0", "project_id": project_id, "tasks": tasks}


def _render_plan(project_id: str, handoff: dict[str, Any], tasks: dict[str, Any]) -> str:
    rows = []
    for task in tasks["tasks"]:
        acceptance = "; ".join(task["acceptance_criteria"])
        verification = task["verification"]["method"]
        rows.append(f"| `{task['task_id']}` | {task['title']} | {acceptance} | {verification} | `PLANNED` |")
    return "\n".join(
        [
            "# PLAN-001",
            "",
            f"**Project ID:** `{project_id}`  ",
            f"**Source Plan:** `{handoff['source_plan']}`  ",
            "**Lifecycle State:** `APPROVED`",
            "",
            "## Tasks",
            "",
            "| Task ID | Task | Acceptance | Verification | Status |",
            "|---|---|---|---|---|",
            *rows,
            "",
            "## Boundaries",
            "",
            "- Execute only the accepted tasks.",
            "- Do not claim completion without evidence-backed verification and closure artifacts.",
            "- Unplanned work requires explicit scope expansion.",
            "",
        ]
    )


def _validate_execution_documents(execution_dir: Path, *, schema_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    state = _load_json(execution_dir / "execution-state.json")
    tasks = _load_json(execution_dir / "tasks.json")
    _validate_document(state, EXECUTION_STATE_SCHEMA, "execution-state.json", schema_root=schema_root)
    _validate_document(tasks, TASK_SCHEMA, "tasks.json", schema_root=schema_root)
    if state["project_id"] != tasks["project_id"]:
        raise ExecutionLifecycleError("execution state and task set project IDs differ")
    history = state["history"]
    if state["sequence"] != history[-1]["sequence"]:
        raise ExecutionLifecycleError("execution sequence must equal the latest history sequence")
    if state["current_state"] != history[-1]["to_state"]:
        raise ExecutionLifecycleError("current_state must equal the latest history state")
    sequences = [item["sequence"] for item in history]
    if sequences != list(range(1, len(sequences) + 1)):
        raise ExecutionLifecycleError("execution history sequence must be contiguous")
    return state, tasks


def _snapshot(paths: list[Path]) -> dict[Path, tuple[bool, bytes | None, int | None]]:
    snapshot: dict[Path, tuple[bool, bytes | None, int | None]] = {}
    for path in paths:
        if path.exists():
            if not path.is_file():
                raise ExecutionLifecycleError(f"transaction path is not a regular file: {path}")
            snapshot[path] = (True, path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        else:
            snapshot[path] = (False, None, None)
    return snapshot


def _restore(snapshot: dict[Path, tuple[bool, bytes | None, int | None]]) -> None:
    for path, (existed, data, mode) in snapshot.items():
        if existed and data is not None:
            atomic_write_bytes(path, data, mode=mode or 0o600)
        elif path.exists():
            path.unlink()


def initialize_execution(
    root: Path,
    handoff_relative: str,
    raw_tasks: list[dict[str, Any]],
    *,
    timestamp: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    _, handoff = _validate_handoff(root, handoff_relative, schema_root=schema_root)
    project_id = handoff["project_id"]
    final_dir = _execution_dir(root, project_id)
    if final_dir.exists():
        raise ExecutionLifecycleError(f"execution workspace already exists: {final_dir}")
    parent = final_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = parent / f".{project_id}.tmp"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    tasks = _normalize_tasks(raw_tasks, project_id, timestamp)
    state = {
        "schema_version": "1.0.0",
        "project_id": project_id,
        "source_handoff": handoff_relative,
        "current_state": "APPROVED",
        "sequence": 1,
        "created_at": timestamp,
        "updated_at": timestamp,
        "history": [
            {
                "sequence": 1,
                "from_state": "PLANNED",
                "to_state": "APPROVED",
                "actor": handoff["approved_by"],
                "reason": "Accepted Intake handoff authorized execution planning.",
                "ts": timestamp,
            }
        ],
        "artifacts": {
            "plan": "PLAN-001.md",
            "tasks": "tasks.json",
            "ledger": "activity_ledger.jsonl",
            "blocker": None,
            "recovery_plan": None,
            "reconciliation": None,
            "summary": None,
            "state_update_proposal": None,
        },
    }
    try:
        atomic_write_json(staging / "execution-state.json", state, mode=0o600)
        atomic_write_json(staging / "tasks.json", tasks, mode=0o600)
        atomic_write_text(staging / "PLAN-001.md", _render_plan(project_id, handoff, tasks), mode=0o600)
        append_event(
            staging / "activity_ledger.jsonl",
            new_event(
                event_id=deterministic_id("EVENT", project_id, 1, "APPROVED"),
                sequence=1,
                phase="plan",
                task_id=project_id,
                artifact="PLAN-001.md",
                status="APPROVED",
                evidence_path=handoff_relative,
                notes="Execution workspace initialized from an explicitly approved Intake handoff.",
                ts=timestamp,
            ),
        )
        _validate_execution_documents(staging, schema_root=schema_root)
        os.replace(staging, final_dir)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return inspect_execution(root, project_id, schema_root=schema_root)


def _load_execution(root: Path, project_id: str, *, schema_root: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    execution_dir = _execution_dir(root, project_id)
    if not execution_dir.is_dir():
        raise ExecutionLifecycleError(f"execution workspace does not exist: {execution_dir}")
    state, tasks = _validate_execution_documents(execution_dir, schema_root=schema_root)
    return execution_dir, state, tasks


def _task_by_id(tasks: dict[str, Any], task_id: str) -> dict[str, Any]:
    task = next((item for item in tasks["tasks"] if item["task_id"] == task_id), None)
    if task is None:
        raise ExecutionLifecycleError(f"unknown task_id: {task_id}")
    return task


def _guard_execution_transition(
    execution_dir: Path,
    state: dict[str, Any],
    tasks: dict[str, Any],
    target_state: str,
    *,
    schema_root: Path,
) -> None:
    current = state["current_state"]
    if target_state not in EXECUTION_STATES:
        raise ExecutionLifecycleError(f"unknown execution state: {target_state}")
    if target_state not in ALLOWED_TRANSITIONS[current]:
        raise ExecutionLifecycleError(f"illegal transition: {current} -> {target_state}")
    statuses = [task["status"] for task in tasks["tasks"]]
    if target_state == "VERIFYING" and any(status not in {"EXECUTED", "VERIFIED"} for status in statuses):
        raise ExecutionLifecycleError("VERIFYING requires every task to be EXECUTED or VERIFIED")
    if target_state == "RECONCILING" and any(status != "VERIFIED" for status in statuses):
        raise ExecutionLifecycleError("RECONCILING requires every task to be VERIFIED")
    if target_state in {"DONE", "DONE_WITH_CONCERNS"}:
        required = ("reconciliation", "summary", "state_update_proposal")
        for key in required:
            relative = state["artifacts"].get(key)
            if not isinstance(relative, str) or not (execution_dir / relative).is_file():
                raise ExecutionLifecycleError(f"terminal completion requires closure artifact: {key}")
        reconciliation = _load_json(execution_dir / state["artifacts"]["reconciliation"])
        _validate_document(reconciliation, RECONCILIATION_SCHEMA, "reconciliation", schema_root=schema_root)


def transition_execution(
    root: Path,
    project_id: str,
    target_state: str,
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
        raise ExecutionLifecycleError("actor and reason must be non-empty")
    execution_dir, state, tasks = _load_execution(root, project_id, schema_root=schema_root)
    _guard_execution_transition(execution_dir, state, tasks, target_state, schema_root=schema_root)
    state_path = execution_dir / "execution-state.json"
    ledger_path = execution_dir / "activity_ledger.jsonl"
    blocker_path = execution_dir / "BLOCKER.md"
    recovery_path = execution_dir / "RECOVERY-PLAN.md"
    paths = [state_path, ledger_path]
    if target_state == "BLOCKED":
        paths.append(blocker_path)
    if target_state == "RECOVERING":
        paths.append(recovery_path)
    snapshot = _snapshot(paths)
    current = state["current_state"]
    sequence = state["sequence"] + 1
    state["current_state"] = target_state
    state["sequence"] = sequence
    state["updated_at"] = timestamp
    state["history"].append(
        {
            "sequence": sequence,
            "from_state": current,
            "to_state": target_state,
            "actor": actor.strip(),
            "reason": reason.strip(),
            "ts": timestamp,
        }
    )
    if target_state == "BLOCKED":
        state["artifacts"]["blocker"] = "BLOCKER.md"
    if target_state == "RECOVERING":
        state["artifacts"]["recovery_plan"] = "RECOVERY-PLAN.md"
    try:
        if target_state == "BLOCKED":
            atomic_write_text(
                blocker_path,
                f"# Blocker\n\n**Project ID:** `{project_id}`  \n**Recorded At:** `{timestamp}`\n\n## Reason\n\n{reason.strip()}\n",
                mode=0o600,
            )
        if target_state == "RECOVERING":
            atomic_write_text(
                recovery_path,
                f"# Recovery Plan\n\n**Project ID:** `{project_id}`  \n**Started At:** `{timestamp}`\n\n## Trigger\n\n{reason.strip()}\n\n## Recovery Target\n\nReturn to a valid lifecycle state without bypassing verification or closure.\n",
                mode=0o600,
            )
        atomic_write_json(state_path, state, mode=0o600)
        append_event(
            ledger_path,
            new_event(
                event_id=deterministic_id("EVENT", project_id, sequence, target_state),
                sequence=len(read_events(ledger_path)) + 1,
                phase="recover" if target_state in {"BLOCKED", "RECOVERING", "NEEDS_CONTEXT"} else target_state.lower(),
                task_id=project_id,
                artifact=state["artifacts"].get("blocker") or state["artifacts"].get("recovery_plan") or "execution-state.json",
                status=target_state,
                evidence_path="execution-state.json",
                notes=reason.strip(),
                ts=timestamp,
            ),
        )
        _validate_execution_documents(execution_dir, schema_root=schema_root)
    except Exception:
        _restore(snapshot)
        raise
    return inspect_execution(root, project_id, schema_root=schema_root)


def transition_task(
    root: Path,
    project_id: str,
    task_id: str,
    target_status: str,
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
        raise ExecutionLifecycleError("actor and reason must be non-empty")
    execution_dir, state, tasks = _load_execution(root, project_id, schema_root=schema_root)
    if state["current_state"] != "EXECUTING":
        raise ExecutionLifecycleError("task transitions require execution state EXECUTING")
    task = _task_by_id(tasks, task_id)
    current = task["status"]
    if target_status not in TASK_TRANSITIONS.get(current, set()):
        raise ExecutionLifecycleError(f"illegal task transition: {current} -> {target_status}")
    tasks_path = execution_dir / "tasks.json"
    ledger_path = execution_dir / "activity_ledger.jsonl"
    snapshot = _snapshot([tasks_path, ledger_path])
    task["status"] = target_status
    task["updated_at"] = timestamp
    try:
        atomic_write_json(tasks_path, tasks, mode=0o600)
        append_event(
            ledger_path,
            new_event(
                event_id=deterministic_id("EVENT", project_id, task_id, target_status, len(read_events(ledger_path)) + 1),
                sequence=len(read_events(ledger_path)) + 1,
                phase="execute",
                task_id=task_id,
                artifact="tasks.json",
                status=target_status,
                evidence_path="PLAN-001.md",
                notes=f"{actor.strip()}: {reason.strip()}",
                ts=timestamp,
            ),
        )
        _validate_execution_documents(execution_dir, schema_root=schema_root)
    except Exception:
        _restore(snapshot)
        raise
    return inspect_execution(root, project_id, schema_root=schema_root)


def record_verification(
    root: Path,
    project_id: str,
    task_id: str,
    *,
    result: str,
    actual_result: str,
    evidence_relative: str,
    timestamp: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    timestamp = timestamp or _now()
    result = result.upper()
    if result not in {"PASS", "FAIL"}:
        raise ExecutionLifecycleError("verification result must be PASS or FAIL")
    if not actual_result.strip():
        raise ExecutionLifecycleError("actual_result must be non-empty")
    execution_dir, state, tasks = _load_execution(root, project_id, schema_root=schema_root)
    if state["current_state"] != "VERIFYING":
        raise ExecutionLifecycleError("verification requires execution state VERIFYING")
    task = _task_by_id(tasks, task_id)
    if task["status"] != "EXECUTED":
        raise ExecutionLifecycleError("verification requires task status EXECUTED")
    evidence_path = _require_relative_file(root, evidence_relative)
    evidence_hash = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    tasks_path = execution_dir / "tasks.json"
    ledger_path = execution_dir / "activity_ledger.jsonl"
    snapshot = _snapshot([tasks_path, ledger_path])
    task["status"] = "VERIFIED" if result == "PASS" else "FAILED"
    task["updated_at"] = timestamp
    task["verification"].update(
        {
            "actual_result": actual_result.strip(),
            "evidence_path": evidence_relative,
            "evidence_hash": evidence_hash,
            "status": result,
            "verified_at": timestamp,
        }
    )
    try:
        atomic_write_json(tasks_path, tasks, mode=0o600)
        append_event(
            ledger_path,
            new_event(
                event_id=deterministic_id("EVENT", project_id, task_id, "verify", len(read_events(ledger_path)) + 1),
                sequence=len(read_events(ledger_path)) + 1,
                phase="verify",
                task_id=task_id,
                artifact="tasks.json",
                status=task["status"],
                evidence_path=evidence_relative,
                notes=actual_result.strip(),
                ts=timestamp,
            ),
        )
        _validate_execution_documents(execution_dir, schema_root=schema_root)
    except Exception:
        _restore(snapshot)
        raise
    return inspect_execution(root, project_id, schema_root=schema_root)


def inspect_execution(root: Path, project_id: str, *, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    execution_dir, state, tasks = _load_execution(root, project_id, schema_root=Path(schema_root).resolve())
    statuses: dict[str, int] = {}
    for task in tasks["tasks"]:
        statuses[task["status"]] = statuses.get(task["status"], 0) + 1
    return {
        "schema_version": "1.0.0",
        "project_id": project_id,
        "execution_dir": _relative_path(root, execution_dir),
        "current_state": state["current_state"],
        "state_sequence": state["sequence"],
        "task_count": len(tasks["tasks"]),
        "task_statuses": statuses,
        "all_tasks_verified": all(task["status"] == "VERIFIED" for task in tasks["tasks"]),
        "ledger_event_count": len(read_events(execution_dir / "activity_ledger.jsonl")),
        "artifacts": state["artifacts"],
    }


def _load_tasks_request(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExecutionLifecycleError(f"cannot load tasks request: {exc}") from exc
    if isinstance(value, dict):
        value = value.get("tasks")
    if not isinstance(value, list):
        raise ExecutionLifecycleError("tasks request must be an array or an object containing tasks")
    return value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("initialize")
    initialize.add_argument("--root", type=Path, default=Path.cwd())
    initialize.add_argument("--handoff", required=True)
    initialize.add_argument("--tasks", type=Path, required=True)

    transition = subparsers.add_parser("transition")
    transition.add_argument("--root", type=Path, default=Path.cwd())
    transition.add_argument("--project-id", required=True)
    transition.add_argument("--to", required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--reason", required=True)

    task = subparsers.add_parser("task")
    task.add_argument("--root", type=Path, default=Path.cwd())
    task.add_argument("--project-id", required=True)
    task.add_argument("--task-id", required=True)
    task.add_argument("--to", required=True)
    task.add_argument("--actor", required=True)
    task.add_argument("--reason", required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--root", type=Path, default=Path.cwd())
    verify.add_argument("--project-id", required=True)
    verify.add_argument("--task-id", required=True)
    verify.add_argument("--result", choices=("PASS", "FAIL"), required=True)
    verify.add_argument("--actual-result", required=True)
    verify.add_argument("--evidence", required=True)

    status = subparsers.add_parser("status")
    status.add_argument("--root", type=Path, default=Path.cwd())
    status.add_argument("--project-id", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.command == "initialize":
            result = initialize_execution(args.root, args.handoff, _load_tasks_request(args.tasks))
        elif args.command == "transition":
            result = transition_execution(args.root, args.project_id, args.to, actor=args.actor, reason=args.reason)
        elif args.command == "task":
            result = transition_task(args.root, args.project_id, args.task_id, args.to, actor=args.actor, reason=args.reason)
        elif args.command == "verify":
            result = record_verification(
                args.root,
                args.project_id,
                args.task_id,
                result=args.result,
                actual_result=args.actual_result,
                evidence_relative=args.evidence,
            )
        else:
            result = inspect_execution(args.root, args.project_id)
    except (ExecutionLifecycleError, OSError) as exc:
        print(f"Creator Execution failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
