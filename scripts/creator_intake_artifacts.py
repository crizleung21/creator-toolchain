#!/usr/bin/env python3
"""Create and inspect canonical Creator Toolchain intake artifact packages."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_ids import deterministic_id
    from creator_ledger import append_event, new_event
    from creator_planning_gate import evaluate_plan, record_gate_result
    from creator_project_types import get_project_type
    from creator_transactions import atomic_write_json, atomic_write_text
except ImportError:  # Imported as scripts.creator_intake_artifacts in tests.
    from scripts.creator_ids import deterministic_id
    from scripts.creator_ledger import append_event, new_event
    from scripts.creator_planning_gate import evaluate_plan, record_gate_result
    from scripts.creator_project_types import get_project_type
    from scripts.creator_transactions import atomic_write_json, atomic_write_text

ARTIFACT_PATHS = {
    "project": "project.json",
    "ledger": "activity_ledger.jsonl",
    "intake_state": "INTAKE-STATE.md",
    "planning": "PLANNING.md",
    "decisions": "DECISIONS.md",
    "open_questions": "OPEN-QUESTIONS.md",
    "handoff": "HANDOFF.md",
}


class IntakeError(RuntimeError):
    """Raised when an intake package cannot be created safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise IntakeError("title does not produce a valid project slug")
    return slug


def _strings(request: dict[str, Any], field: str) -> list[str]:
    value = request.get(field, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise IntakeError(f"{field} must be an array of strings")
    return [item.strip() for item in value if item.strip()]


def _criteria(request: dict[str, Any]) -> list[dict[str, str]]:
    value = request.get("acceptance_criteria", [])
    if not isinstance(value, list):
        raise IntakeError("acceptance_criteria must be an array")
    result: list[dict[str, str]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise IntakeError(f"acceptance_criteria[{index - 1}] must be an object")
        result.append(
            {
                "id": str(item.get("id") or f"AC-{index}"),
                "title": str(item.get("title") or f"Criterion {index}"),
                "given": str(item.get("given") or "").strip(),
                "when": str(item.get("when") or "").strip(),
                "then": str(item.get("then") or "").strip(),
            }
        )
    return result


def _bullets(items: list[str], *, empty: str = "none") -> str:
    return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"


def _render_planning(
    request: dict[str, Any],
    *,
    project_id: str,
    project_type: str,
    source_assets: list[str],
    scope: list[str],
    out_of_scope: list[str],
    risks: list[str],
    criteria: list[dict[str, str]],
) -> str:
    criterion_text = []
    for item in criteria:
        criterion_text.append(
            "\n".join(
                [
                    f"### {item['id']}: {item['title']}",
                    "",
                    f"- Given {item['given']}",
                    f"- When {item['when']}",
                    f"- Then {item['then']}",
                ]
            )
        )
    return f"""# {request['title']}

**Project ID:** `{project_id}`

## Goal

{request.get('goal', '').strip()}

## Project Type

`{project_type}`

## Context

{request.get('context', '').strip()}

## Source Assets

{_bullets(source_assets)}

## Scope

{_bullets(scope)}

## Out of Scope

{_bullets(out_of_scope)}

## Acceptance Criteria

{chr(10).join(criterion_text)}

## Risks

{_bullets(risks)}

## Open Questions

See `OPEN-QUESTIONS.md`.

## Handoff Target

`creator-execution-cycle`
"""


def _render_questions(blocking: list[str], non_blocking: list[str]) -> str:
    return f"""# Open Questions

## Blocking

{_bullets(blocking)}

## Non-Blocking

{_bullets(non_blocking)}
"""


def _render_intake_state(
    *,
    project_id: str,
    stage: str,
    gate_result: str,
    answered: list[str],
    unanswered: list[str],
    blocking: list[str],
    non_blocking: list[str],
    updated_at: str,
) -> str:
    if blocking:
        next_prompt = "Resolve the blocking questions before scaffolding or handoff."
    elif gate_result == "pass_with_non_blocking_questions":
        next_prompt = "Review non-blocking questions, then approve scaffold or execution handoff."
    elif gate_result == "pass":
        next_prompt = "Approve scaffold-only or handoff-to-execution."
    else:
        next_prompt = "Continue typed planning until the Planning Quality Gate passes."
    return f"""# Intake State

**Project ID:** `{project_id}`  
**Stage:** `{stage}`  
**Quality Gate:** `{gate_result}`  
**Last Updated:** `{updated_at}`

## Answered Sections

{_bullets(answered)}

## Unanswered Sections

{_bullets(unanswered)}

## Blocking Questions

{_bullets(blocking)}

## Non-Blocking Questions

{_bullets(non_blocking)}

## Next Prompt

{next_prompt}
"""


def _handoff_decision(gate_result: str, approval_status: str) -> str:
    if gate_result == "fail_needs_more_planning":
        return "planning-required"
    if approval_status == "approved":
        return "handoff-to-execution"
    return "scaffold-only"


def _render_handoff(
    request: dict[str, Any],
    *,
    project_id: str,
    gate_result: str,
    approval_status: str,
    open_questions: list[str],
    risks: list[str],
    criteria: list[dict[str, str]],
    updated_at: str,
) -> str:
    criteria_lines = [f"{item['id']}: {item['then'] or item['title']}" for item in criteria]
    return f"""# Handoff

**Project ID:** `{project_id}`  
**Updated At:** `{updated_at}`

## Source Plan

`PLANNING.md`

## Accepted MVP

{request.get('goal', '').strip()}

## First Execution Phase

Create a bounded execution plan from the accepted Intake package. Do not expand scope silently.

## Acceptance Criteria

{_bullets(criteria_lines)}

## Risks

{_bullets(risks)}

## Open Questions

{_bullets(open_questions)}

## Target Skill

`creator-execution-cycle`

## Quality Gate Result

`{gate_result}`

## Approval Status

`{approval_status}`

## Handoff Decision

`{_handoff_decision(gate_result, approval_status)}`
"""


def _render_decisions(project_id: str, timestamp: str) -> str:
    return f"""# Decisions

**Project ID:** `{project_id}`  
**Last Updated:** `{timestamp}`

No project-specific decisions have been recorded.
"""


def _validate_request(request: dict[str, Any], *, registry_root: Path) -> tuple[str, dict[str, Any]]:
    title = request.get("title")
    project_type = request.get("project_type")
    if not isinstance(title, str) or not title.strip():
        raise IntakeError("title must be a non-empty string")
    if not isinstance(project_type, str) or not project_type:
        raise IntakeError("project_type must be a non-empty string")
    contract = get_project_type(project_type, registry_root)
    approval = request.get("approval_status", "pending")
    if approval not in {"pending", "approved", "rejected"}:
        raise IntakeError("approval_status must be pending, approved, or rejected")
    return project_type, contract


def create_intake_package(
    root: Path,
    request: dict[str, Any],
    *,
    timestamp: str | None = None,
    registry_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    registry_root = Path(registry_root).resolve() if registry_root else Path(__file__).resolve().parents[1]
    project_type, contract = _validate_request(request, registry_root=registry_root)
    timestamp = timestamp or _now()
    slug = slugify(request["title"])
    project_id = deterministic_id("PROJECT", slug, project_type)
    plans_root = root / ".creator/plans"
    final_dir = plans_root / slug
    if final_dir.exists():
        raise IntakeError(f"intake package already exists: {final_dir}")
    plans_root.mkdir(parents=True, exist_ok=True)
    staging = plans_root / f".{slug}.{project_id}.tmp"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()

    source_assets = _strings(request, "source_assets")
    scope = _strings(request, "scope")
    out_of_scope = _strings(request, "out_of_scope")
    risks = _strings(request, "risks")
    blocking = _strings(request, "blocking_questions")
    non_blocking = _strings(request, "non_blocking_questions")
    criteria = _criteria(request)
    approval_status = str(request.get("approval_status", "pending"))

    project = {
        "schema_version": "0.4.0",
        "project_id": project_id,
        "slug": slug,
        "title": request["title"].strip(),
        "project_type": project_type,
        "rigor": contract["rigor"],
        "stage": "ideating",
        "approval_status": approval_status,
        "quality_gate_result": "not_evaluated",
        "handoff_target": "creator-execution-cycle",
        "source_assets": source_assets,
        "artifact_paths": ARTIFACT_PATHS,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    try:
        atomic_write_json(staging / "project.json", project, mode=0o600)
        atomic_write_text(
            staging / "PLANNING.md",
            _render_planning(
                request,
                project_id=project_id,
                project_type=project_type,
                source_assets=source_assets,
                scope=scope,
                out_of_scope=out_of_scope,
                risks=risks,
                criteria=criteria,
            ),
            mode=0o600,
        )
        atomic_write_text(staging / "DECISIONS.md", _render_decisions(project_id, timestamp), mode=0o600)
        atomic_write_text(
            staging / "OPEN-QUESTIONS.md",
            _render_questions(blocking, non_blocking),
            mode=0o600,
        )
        atomic_write_text(
            staging / "INTAKE-STATE.md",
            _render_intake_state(
                project_id=project_id,
                stage="ideating",
                gate_result="not_evaluated",
                answered=[],
                unanswered=[],
                blocking=blocking,
                non_blocking=non_blocking,
                updated_at=timestamp,
            ),
            mode=0o600,
        )
        atomic_write_text(
            staging / "HANDOFF.md",
            _render_handoff(
                request,
                project_id=project_id,
                gate_result="not_evaluated",
                approval_status=approval_status,
                open_questions=blocking + non_blocking,
                risks=risks,
                criteria=criteria,
                updated_at=timestamp,
            ),
            mode=0o600,
        )
        append_event(
            staging / "activity_ledger.jsonl",
            new_event(
                event_id=deterministic_id("EVENT", project_id, "intake-start"),
                sequence=1,
                phase="intake",
                task_id=project_id,
                artifact="project.json",
                status="IN_PROGRESS",
                evidence_path="PLANNING.md",
                notes="Canonical Intake package created transactionally.",
                ts=timestamp,
            ),
        )

        report = evaluate_plan(staging, workspace_root=root, evaluated_at=timestamp)
        record_gate_result(staging, report)
        project = json.loads((staging / "project.json").read_text(encoding="utf-8"))
        answered = [
            heading
            for heading in (
                "Goal",
                "Project Type",
                "Context",
                "Scope",
                "Out of Scope",
                "Acceptance Criteria",
                "Risks",
                "Open Questions",
                "Handoff Target",
            )
            if not any(
                item["check_id"] == "GATE_SECTION" and repr(heading) in item["message"]
                for item in report["findings"]
            )
        ]
        unanswered = [
            heading
            for heading in (
                "Goal",
                "Project Type",
                "Context",
                "Scope",
                "Out of Scope",
                "Acceptance Criteria",
                "Risks",
                "Open Questions",
                "Handoff Target",
            )
            if heading not in answered
        ]
        atomic_write_text(
            staging / "INTAKE-STATE.md",
            _render_intake_state(
                project_id=project_id,
                stage=project["stage"],
                gate_result=report["result"],
                answered=answered,
                unanswered=unanswered,
                blocking=blocking,
                non_blocking=non_blocking,
                updated_at=timestamp,
            ),
            mode=0o600,
        )
        atomic_write_text(
            staging / "HANDOFF.md",
            _render_handoff(
                request,
                project_id=project_id,
                gate_result=report["result"],
                approval_status=approval_status,
                open_questions=blocking + non_blocking,
                risks=risks,
                criteria=criteria,
                updated_at=timestamp,
            ),
            mode=0o600,
        )
        gate_status = {
            "pass": "DONE",
            "pass_with_non_blocking_questions": "DONE_WITH_CONCERNS",
            "fail_needs_more_planning": "NEEDS_CONTEXT",
        }[report["result"]]
        append_event(
            staging / "activity_ledger.jsonl",
            new_event(
                event_id=deterministic_id("EVENT", project_id, "planning-gate"),
                sequence=2,
                phase="gate",
                task_id=project_id,
                artifact="PLANNING.md",
                status=gate_status,
                evidence_path="OPEN-QUESTIONS.md",
                notes=f"Planning Quality Gate result: {report['result']}.",
                ts=timestamp,
            ),
        )
        os.replace(staging, final_dir)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return {**report, "plan_dir": str(final_dir), "slug": slug}


def inspect_intake_package(root: Path, slug: str) -> dict[str, Any]:
    root = Path(root).resolve()
    plan_dir = root / ".creator/plans" / slugify(slug)
    if not plan_dir.is_dir():
        raise IntakeError(f"intake package does not exist: {plan_dir}")
    return {**evaluate_plan(plan_dir, workspace_root=root), "plan_dir": str(plan_dir), "slug": plan_dir.name}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--root", type=Path, default=Path.cwd())
    create.add_argument("--request", type=Path, required=True)
    status = subparsers.add_parser("status")
    status.add_argument("--root", type=Path, default=Path.cwd())
    status.add_argument("--project", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.command == "create":
            request = json.loads(args.request.read_text(encoding="utf-8"))
            if not isinstance(request, dict):
                raise IntakeError("request root must be an object")
            result = create_intake_package(args.root, request)
        else:
            result = inspect_intake_package(args.root, args.project)
    except (IntakeError, OSError, json.JSONDecodeError) as exc:
        print(f"Creator Intake failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["result"] != "fail_needs_more_planning" else 1


if __name__ == "__main__":
    raise SystemExit(main())
