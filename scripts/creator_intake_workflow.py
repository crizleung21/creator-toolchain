#!/usr/bin/env python3
"""Approve, scaffold, and hand off Creator Toolchain intake packages safely."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from creator_ids import deterministic_id
    from creator_ledger import append_event, new_event, read_events
    from creator_planning_gate import evaluate_plan
    from creator_transactions import atomic_write_json, atomic_write_text
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:  # Imported as scripts.creator_intake_workflow in tests.
    from scripts.creator_ids import deterministic_id
    from scripts.creator_ledger import append_event, new_event, read_events
    from scripts.creator_planning_gate import evaluate_plan
    from scripts.creator_transactions import atomic_write_json, atomic_write_text
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
PROJECT_SCHEMA = ROOT / "schemas/project/project.schema.json"
PROPOSAL_SCHEMA = ROOT / "schemas/project/state-registration-proposal.schema.json"
HANDOFF_SCHEMA = ROOT / "schemas/project/execution-handoff.schema.json"
APPROVAL_DECISIONS = {"scaffold-only", "handoff-to-execution"}
SCAFFOLD_FILES = {"PROJECT.md", "README.md", "HANDOFF.md"}


class IntakeWorkflowError(RuntimeError):
    """Raised when an Intake workflow transition is invalid or unsafe."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise IntakeWorkflowError("project does not produce a valid slug")
    return slug


def _repo_relative(root: Path, path: Path) -> Path:
    root = Path(root).resolve()
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(root)
    except ValueError as exc:
        raise IntakeWorkflowError(f"path must remain inside the workspace: {resolved}") from exc


def _plan_dir(root: Path, project: str) -> Path:
    root = Path(root).resolve()
    candidate = root / ".creator/plans" / _slug(project)
    if not candidate.is_dir():
        raise IntakeWorkflowError(f"intake package does not exist: {candidate}")
    return candidate


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntakeWorkflowError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IntakeWorkflowError(f"JSON root must be an object: {path}")
    return value


def _validate_json(value: dict[str, Any], schema_path: Path, label: str) -> None:
    findings = validate_json_schema(value, load_schema(schema_path))
    if findings:
        raise IntakeWorkflowError(f"{label} validation failed: {'; '.join(findings)}")


def _sections(text: str, *, level: int = 2) -> dict[str, str]:
    marker = "#" * level
    pattern = re.compile(rf"(?m)^{re.escape(marker)}\s+(.+?)\s*$")
    matches = list(pattern.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1).strip()] = text[start:end].strip()
    return result


def _bullet_items(body: str) -> list[str]:
    result: list[str] = []
    for line in body.splitlines():
        match = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if match:
            value = match.group(1).strip()
            if value.lower().rstrip(".") not in {"none", "n/a"}:
                result.append(value)
    return result


def _questions(plan_dir: Path) -> tuple[list[str], list[str]]:
    sections = _sections((plan_dir / "OPEN-QUESTIONS.md").read_text(encoding="utf-8"))
    return _bullet_items(sections.get("Blocking", "")), _bullet_items(sections.get("Non-Blocking", ""))


def _next_sequence(plan_dir: Path) -> int:
    events = read_events(plan_dir / "activity_ledger.jsonl")
    return events[-1]["sequence"] + 1 if events else 1


def _copy_plan_for_update(plan_dir: Path, token: str) -> Path:
    staging = plan_dir.parent / f".{plan_dir.name}.{token}.tmp"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(plan_dir, staging)
    return staging


def _hidden_staging(destination: Path, token: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination.parent / f".{destination.name}.{token}.tmp"


def _commit_bundle(replacements: Iterable[tuple[Path, Path]], token: str) -> None:
    items = list(replacements)
    backups: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        for staged, destination in items:
            if not staged.exists():
                raise IntakeWorkflowError(f"staged output is missing: {staged}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                backup = destination.parent / f".{destination.name}.{token}.bak"
                if backup.exists():
                    if backup.is_dir():
                        shutil.rmtree(backup)
                    else:
                        backup.unlink()
                os.replace(destination, backup)
                backups.append((backup, destination))
            os.replace(staged, destination)
            installed.append(destination)
    except Exception as exc:
        for destination in reversed(installed):
            if destination.exists():
                if destination.is_dir():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
        for backup, destination in reversed(backups):
            if backup.exists():
                os.replace(backup, destination)
        raise IntakeWorkflowError(f"bundle commit failed: {exc}") from exc
    else:
        for backup, _ in backups:
            if backup.exists():
                if backup.is_dir():
                    shutil.rmtree(backup)
                else:
                    backup.unlink()


def _cleanup(paths: Iterable[Path]) -> None:
    for path in paths:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def _decision_markdown(
    *, project_id: str, decision_id: str, decision: str, actor: str, timestamp: str
) -> str:
    return f"""

## {decision_id}

- Project ID: `{project_id}`
- Decision: `{decision}`
- Actor: `{actor}`
- Approved At: `{timestamp}`
- Status: `accepted`
- Rationale: The Planning Quality Gate passed and explicit authorization was recorded.
"""


def _render_intake_state(
    *, project_id: str, stage: str, gate_result: str, decision: str | None,
    blocking: list[str], non_blocking: list[str], timestamp: str
) -> str:
    if blocking:
        next_prompt = "Resolve all blocking questions before approval."
    elif decision == "scaffold-only" and stage == "planned":
        next_prompt = "Run the approved scaffold-only operation."
    elif decision == "handoff-to-execution" and stage == "planned":
        next_prompt = "Generate the approved creator-execution-cycle handoff."
    elif stage == "graduated":
        next_prompt = "Review the generated output and submit the state-registration proposal to creator-workspace-manager."
    else:
        next_prompt = "Record explicit approval after the Planning Quality Gate passes."
    bullets = lambda values: "\n".join(f"- {item}" for item in values) if values else "- none"
    return f"""# Intake State

**Project ID:** `{project_id}`  
**Stage:** `{stage}`  
**Quality Gate:** `{gate_result}`  
**Approval Decision:** `{decision or 'pending'}`  
**Last Updated:** `{timestamp}`

## Answered Sections

- Goal
- Project Type
- Context
- Scope
- Out of Scope
- Acceptance Criteria
- Risks
- Open Questions
- Handoff Target

## Unanswered Sections

- none

## Blocking Questions

{bullets(blocking)}

## Non-Blocking Questions

{bullets(non_blocking)}

## Next Prompt

{next_prompt}
"""


def _render_handoff_markdown(
    *, project: dict[str, Any], decision: str, actor: str, gate_result: str,
    blocking: list[str], non_blocking: list[str], timestamp: str
) -> str:
    bullets = lambda values: "\n".join(f"- {item}" for item in values) if values else "- none"
    target = "creator-execution-cycle" if decision == "handoff-to-execution" else "not-authorized"
    return f"""# Handoff

**Project ID:** `{project['project_id']}`  
**Updated At:** `{timestamp}`

## Source Plan

`PLANNING.md`

## Target Skill

`{target}`

## Quality Gate Result

`{gate_result}`

## Approval Status

`approved`

## Approval Decision

`{decision}`

## Approved By

`{actor}`

## Open Questions

### Blocking

{bullets(blocking)}

### Non-Blocking

{bullets(non_blocking)}

## Handoff Decision

`{decision}`
"""


def _registration_proposal(
    *, root: Path, project: dict[str, Any], timestamp: str, proposal_path: str
) -> dict[str, Any]:
    slug = project["slug"]
    record_status = "approved" if project.get("approval_decision") == "handoff-to-execution" else "planned"
    return {
        "schema_version": "1.0.0",
        "proposal_id": deterministic_id("PROPOSAL", project["project_id"], "register-project"),
        "operation": "register-project",
        "status": "staged",
        "target_surface": ".creator/projects.json",
        "owner_skill": "creator-workspace-manager",
        "requested_by": "creator-intake-planner",
        "source_plan": f".creator/plans/{slug}/PLANNING.md",
        "proposal_path": proposal_path,
        "project": {
            "project_id": project["project_id"],
            "title": project["title"],
            "project_type": project["project_type"],
            "status": record_status,
            "plan_path": f".creator/plans/{slug}/PLANNING.md",
            "last_summary": None,
            "created_at": project["created_at"],
            "updated_at": timestamp,
        },
        "evidence_paths": [
            f".creator/plans/{slug}/project.json",
            f".creator/plans/{slug}/PLANNING.md",
            f".creator/plans/{slug}/HANDOFF.md",
            f".creator/plans/{slug}/activity_ledger.jsonl",
        ],
        "created_at": project.get("approved_at") or timestamp,
        "updated_at": timestamp,
    }


def _write_proposal_stage(root: Path, project: dict[str, Any], timestamp: str, token: str) -> tuple[Path, Path]:
    relative = f".creator/state-proposals/{project['project_id']}.json"
    destination = root / relative
    staged = _hidden_staging(destination, token)
    proposal = _registration_proposal(root=root, project=project, timestamp=timestamp, proposal_path=relative)
    _validate_json(proposal, PROPOSAL_SCHEMA, "state-registration proposal")
    atomic_write_json(staged, proposal, mode=0o600)
    return staged, destination


def approve_intake(
    root: Path, project: str, *, actor: str, decision: str, timestamp: str | None = None
) -> dict[str, Any]:
    root = Path(root).resolve()
    if decision not in APPROVAL_DECISIONS:
        raise IntakeWorkflowError(f"decision must be one of {sorted(APPROVAL_DECISIONS)}")
    if not actor.strip():
        raise IntakeWorkflowError("actor must be a non-empty string")
    timestamp = timestamp or _now()
    plan_dir = _plan_dir(root, project)
    gate = evaluate_plan(plan_dir, workspace_root=root, evaluated_at=timestamp)
    if gate["result"] == "fail_needs_more_planning":
        raise IntakeWorkflowError("Planning Quality Gate must pass before approval")
    current = _load_json(plan_dir / "project.json")
    if current.get("approval_status") == "approved":
        raise IntakeWorkflowError("project is already approved")
    token = deterministic_id("TX", current["project_id"], "approve", decision, timestamp)
    staged_plan = _copy_plan_for_update(plan_dir, token)
    cleanup = [staged_plan]
    try:
        project_data = _load_json(staged_plan / "project.json")
        project_data.update(
            {
                "approval_status": "approved",
                "approval_decision": decision,
                "approved_by": actor.strip(),
                "approved_at": timestamp,
                "state_registration_proposal_path": f".creator/state-proposals/{project_data['project_id']}.json",
                "updated_at": timestamp,
            }
        )
        _validate_json(project_data, PROJECT_SCHEMA, "project")
        atomic_write_json(staged_plan / "project.json", project_data, mode=0o600)
        blocking, non_blocking = _questions(staged_plan)
        decision_id = deterministic_id("DECISION", project_data["project_id"], actor.strip(), decision)
        decisions = (staged_plan / "DECISIONS.md").read_text(encoding="utf-8").rstrip()
        atomic_write_text(
            staged_plan / "DECISIONS.md",
            decisions + _decision_markdown(
                project_id=project_data["project_id"],
                decision_id=decision_id,
                decision=decision,
                actor=actor.strip(),
                timestamp=timestamp,
            ) + "\n",
            mode=0o600,
        )
        atomic_write_text(
            staged_plan / "INTAKE-STATE.md",
            _render_intake_state(
                project_id=project_data["project_id"], stage="planned", gate_result=gate["result"],
                decision=decision, blocking=blocking, non_blocking=non_blocking, timestamp=timestamp,
            ),
            mode=0o600,
        )
        atomic_write_text(
            staged_plan / "HANDOFF.md",
            _render_handoff_markdown(
                project=project_data, decision=decision, actor=actor.strip(), gate_result=gate["result"],
                blocking=blocking, non_blocking=non_blocking, timestamp=timestamp,
            ),
            mode=0o600,
        )
        append_event(
            staged_plan / "activity_ledger.jsonl",
            new_event(
                event_id=deterministic_id("EVENT", project_data["project_id"], "approval", decision),
                sequence=_next_sequence(staged_plan), phase="approval", task_id=project_data["project_id"],
                artifact="DECISIONS.md", status="DONE", evidence_path="HANDOFF.md",
                notes=f"Explicit approval recorded: {decision} by {actor.strip()}.", ts=timestamp,
            ),
        )
        post_gate = evaluate_plan(staged_plan, workspace_root=root, evaluated_at=timestamp)
        if post_gate["result"] == "fail_needs_more_planning":
            raise IntakeWorkflowError("approval mutation made the Intake package invalid")
        staged_proposal, proposal_destination = _write_proposal_stage(root, project_data, timestamp, token)
        cleanup.append(staged_proposal)
        _commit_bundle([(staged_plan, plan_dir), (staged_proposal, proposal_destination)], token)
        cleanup.clear()
    finally:
        _cleanup(cleanup)
    return {
        "project_id": current["project_id"],
        "result": "approved",
        "decision": decision,
        "quality_gate_result": gate["result"],
        "state_registration_proposal": str(proposal_destination),
    }


def _approved_project(root: Path, project: str, required_decision: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    plan_dir = _plan_dir(root, project)
    gate = evaluate_plan(plan_dir, workspace_root=root)
    if gate["result"] == "fail_needs_more_planning":
        raise IntakeWorkflowError("Planning Quality Gate no longer passes")
    data = _load_json(plan_dir / "project.json")
    if data.get("approval_status") != "approved" or data.get("approval_decision") != required_decision:
        raise IntakeWorkflowError(f"operation requires approved decision {required_decision!r}")
    return plan_dir, data, gate


def scaffold_intake(
    root: Path, project: str, *, output: Path | None = None, timestamp: str | None = None
) -> dict[str, Any]:
    root = Path(root).resolve()
    timestamp = timestamp or _now()
    plan_dir, current, gate = _approved_project(root, project, "scaffold-only")
    destination = Path(output).resolve() if output else root / ".creator/scaffolds" / current["slug"]
    destination_relative = _repo_relative(root, destination)
    if destination.exists():
        raise IntakeWorkflowError(f"scaffold already exists: {destination}")
    token = deterministic_id("TX", current["project_id"], "scaffold", timestamp)
    staged_plan = _copy_plan_for_update(plan_dir, token)
    staged_scaffold = _hidden_staging(destination, token)
    cleanup = [staged_plan, staged_scaffold]
    try:
        staged_scaffold.mkdir(parents=True)
        planning = (staged_plan / "PLANNING.md").read_text(encoding="utf-8")
        plan_sections = _sections(planning)
        atomic_write_text(
            staged_scaffold / "PROJECT.md",
            f"""# {current['title']}\n\n**Project ID:** `{current['project_id']}`\n\n## Goal\n\n{plan_sections.get('Goal','')}\n\n## Scope\n\n{plan_sections.get('Scope','')}\n\n## Out of Scope\n\n{plan_sections.get('Out of Scope','')}\n\n## Acceptance Criteria\n\n{plan_sections.get('Acceptance Criteria','')}\n""",
            mode=0o600,
        )
        atomic_write_text(
            staged_scaffold / "README.md",
            f"""# {current['title']} Scaffold\n\nThis is a planning-only scaffold generated from `.creator/plans/{current['slug']}/PLANNING.md`.\n\nNo implementation files have been created. Execution requires a separately approved `handoff-to-execution` decision.\n""",
            mode=0o600,
        )
        atomic_write_text(
            staged_scaffold / "HANDOFF.md",
            f"""# Scaffold Handoff\n\n- Project ID: `{current['project_id']}`\n- Decision: `scaffold-only`\n- Source plan: `.creator/plans/{current['slug']}/PLANNING.md`\n- Execution authorized: `false`\n- Generated at: `{timestamp}`\n""",
            mode=0o600,
        )
        if {path.name for path in staged_scaffold.iterdir()} != SCAFFOLD_FILES:
            raise IntakeWorkflowError("scaffold contains unexpected files")
        project_data = _load_json(staged_plan / "project.json")
        project_data.update({"stage": "graduated", "scaffold_path": destination_relative.as_posix(), "updated_at": timestamp})
        _validate_json(project_data, PROJECT_SCHEMA, "project")
        atomic_write_json(staged_plan / "project.json", project_data, mode=0o600)
        blocking, non_blocking = _questions(staged_plan)
        atomic_write_text(
            staged_plan / "INTAKE-STATE.md",
            _render_intake_state(
                project_id=project_data["project_id"], stage="graduated", gate_result=gate["result"],
                decision="scaffold-only", blocking=blocking, non_blocking=non_blocking, timestamp=timestamp,
            ),
            mode=0o600,
        )
        append_event(
            staged_plan / "activity_ledger.jsonl",
            new_event(
                event_id=deterministic_id("EVENT", project_data["project_id"], "scaffold"),
                sequence=_next_sequence(staged_plan), phase="scaffold", task_id=project_data["project_id"],
                artifact=(destination_relative / "PROJECT.md").as_posix(), status="DONE",
                evidence_path=(destination_relative / "README.md").as_posix(),
                notes="Planning-only scaffold generated; execution remains unauthorized.", ts=timestamp,
            ),
        )
        staged_proposal, proposal_destination = _write_proposal_stage(root, project_data, timestamp, token)
        cleanup.append(staged_proposal)
        _commit_bundle(
            [(staged_plan, plan_dir), (staged_scaffold, destination), (staged_proposal, proposal_destination)], token
        )
        cleanup.clear()
    finally:
        _cleanup(cleanup)
    return {"project_id": current["project_id"], "result": "scaffolded", "scaffold_path": str(destination)}


def handoff_intake(root: Path, project: str, *, timestamp: str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    timestamp = timestamp or _now()
    plan_dir, current, gate = _approved_project(root, project, "handoff-to-execution")
    relative = f".creator/handoffs/{current['project_id']}.json"
    destination = root / relative
    if destination.exists():
        raise IntakeWorkflowError(f"execution handoff already exists: {destination}")
    token = deterministic_id("TX", current["project_id"], "handoff", timestamp)
    staged_plan = _copy_plan_for_update(plan_dir, token)
    staged_handoff = _hidden_staging(destination, token)
    cleanup = [staged_plan, staged_handoff]
    try:
        project_data = _load_json(staged_plan / "project.json")
        project_data.update({"stage": "graduated", "execution_handoff_path": relative, "updated_at": timestamp})
        _validate_json(project_data, PROJECT_SCHEMA, "project")
        atomic_write_json(staged_plan / "project.json", project_data, mode=0o600)
        blocking, non_blocking = _questions(staged_plan)
        payload = {
            "schema_version": "1.0.0",
            "project_id": project_data["project_id"],
            "source_plan": f".creator/plans/{project_data['slug']}/PLANNING.md",
            "target_skill": "creator-execution-cycle",
            "quality_gate_result": gate["result"],
            "approval_status": "approved",
            "approval_decision": "handoff-to-execution",
            "approved_by": project_data["approved_by"],
            "approved_at": project_data["approved_at"],
            "artifact_paths": [f".creator/plans/{project_data['slug']}/{name}" for name in sorted({"project.json","activity_ledger.jsonl","INTAKE-STATE.md","PLANNING.md","DECISIONS.md","OPEN-QUESTIONS.md","HANDOFF.md"})],
            "open_questions": non_blocking,
            "generated_at": timestamp,
        }
        _validate_json(payload, HANDOFF_SCHEMA, "execution handoff")
        atomic_write_json(staged_handoff, payload, mode=0o600)
        atomic_write_text(
            staged_plan / "HANDOFF.md",
            _render_handoff_markdown(
                project=project_data, decision="handoff-to-execution", actor=project_data["approved_by"],
                gate_result=gate["result"], blocking=blocking, non_blocking=non_blocking, timestamp=timestamp,
            ),
            mode=0o600,
        )
        atomic_write_text(
            staged_plan / "INTAKE-STATE.md",
            _render_intake_state(
                project_id=project_data["project_id"], stage="graduated", gate_result=gate["result"],
                decision="handoff-to-execution", blocking=blocking, non_blocking=non_blocking, timestamp=timestamp,
            ),
            mode=0o600,
        )
        append_event(
            staged_plan / "activity_ledger.jsonl",
            new_event(
                event_id=deterministic_id("EVENT", project_data["project_id"], "execution-handoff"),
                sequence=_next_sequence(staged_plan), phase="handoff", task_id=project_data["project_id"],
                artifact=relative, status="DONE", evidence_path="HANDOFF.md",
                notes="Validated execution handoff generated for creator-execution-cycle.", ts=timestamp,
            ),
        )
        staged_proposal, proposal_destination = _write_proposal_stage(root, project_data, timestamp, token)
        cleanup.append(staged_proposal)
        _commit_bundle(
            [(staged_plan, plan_dir), (staged_handoff, destination), (staged_proposal, proposal_destination)], token
        )
        cleanup.clear()
    finally:
        _cleanup(cleanup)
    return {"project_id": current["project_id"], "result": "handed-off", "execution_handoff_path": str(destination)}


def inspect_registration_proposal(root: Path, project: str) -> dict[str, Any]:
    root = Path(root).resolve()
    plan_dir = _plan_dir(root, project)
    project_data = _load_json(plan_dir / "project.json")
    path = root / ".creator/state-proposals" / f"{project_data['project_id']}.json"
    proposal = _load_json(path)
    _validate_json(proposal, PROPOSAL_SCHEMA, "state-registration proposal")
    return proposal


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    approve = sub.add_parser("approve")
    approve.add_argument("--root", type=Path, default=Path.cwd())
    approve.add_argument("--project", required=True)
    approve.add_argument("--actor", required=True)
    approve.add_argument("--decision", choices=sorted(APPROVAL_DECISIONS), required=True)
    scaffold = sub.add_parser("scaffold")
    scaffold.add_argument("--root", type=Path, default=Path.cwd())
    scaffold.add_argument("--project", required=True)
    scaffold.add_argument("--output", type=Path)
    handoff = sub.add_parser("handoff")
    handoff.add_argument("--root", type=Path, default=Path.cwd())
    handoff.add_argument("--project", required=True)
    proposal = sub.add_parser("proposal")
    proposal.add_argument("--root", type=Path, default=Path.cwd())
    proposal.add_argument("--project", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.command == "approve":
            result = approve_intake(args.root, args.project, actor=args.actor, decision=args.decision)
        elif args.command == "scaffold":
            result = scaffold_intake(args.root, args.project, output=args.output)
        elif args.command == "handoff":
            result = handoff_intake(args.root, args.project)
        else:
            result = inspect_registration_proposal(args.root, args.project)
    except (IntakeWorkflowError, OSError, json.JSONDecodeError) as exc:
        print(f"Creator Intake workflow failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
