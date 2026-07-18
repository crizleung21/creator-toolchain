#!/usr/bin/env python3
"""Evaluate Creator Toolchain intake plans against deterministic quality gates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_transactions import atomic_write_json
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:  # Imported as scripts.creator_planning_gate in tests.
    from scripts.creator_transactions import atomic_write_json
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
PROJECT_SCHEMA = ROOT / "schemas/project/project.schema.json"
REQUIRED_ARTIFACTS = {
    "project.json",
    "activity_ledger.jsonl",
    "INTAKE-STATE.md",
    "PLANNING.md",
    "DECISIONS.md",
    "OPEN-QUESTIONS.md",
    "HANDOFF.md",
}
REQUIRED_PLAN_SECTIONS = (
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
RESULTS = {
    "pass",
    "pass_with_non_blocking_questions",
    "fail_needs_more_planning",
}


@dataclass(frozen=True, order=True)
class GateFinding:
    check_id: str
    path: str
    message: str
    severity: str = "error"


class PlanningGateError(RuntimeError):
    """Raised when a plan cannot be evaluated safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PlanningGateError(f"cannot read {path}: {exc}") from exc


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


def _question_items(text: str, heading: str) -> list[str]:
    body = _sections(text).get(heading, "")
    result: list[str] = []
    for line in body.splitlines():
        match = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if value.lower().rstrip(".") not in {"none", "n/a"}:
            result.append(value)
    return result


def _acceptance_findings(body: str) -> tuple[int, list[GateFinding]]:
    headings = list(re.finditer(r"(?m)^###\s+(AC-[A-Za-z0-9_-]+)(?::\s*(.*))?\s*$", body))
    findings: list[GateFinding] = []
    valid_count = 0
    if len(headings) < 3:
        findings.append(
            GateFinding(
                "GATE_ACCEPTANCE_COUNT",
                "PLANNING.md",
                "Acceptance Criteria must contain at least three AC-* blocks.",
            )
        )
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        block = body[start:end]
        criterion_id = heading.group(1)
        missing: list[str] = []
        for keyword in ("Given", "When", "Then"):
            if re.search(rf"(?mi)^\s*[-*]\s+{keyword}\s+\S.+$", block) is None:
                missing.append(keyword)
        if missing:
            findings.append(
                GateFinding(
                    "GATE_ACCEPTANCE_OBSERVABLE",
                    "PLANNING.md",
                    f"{criterion_id} is missing observable fields: {', '.join(missing)}.",
                )
            )
        else:
            valid_count += 1
    return valid_count, findings


def evaluate_plan(
    plan_dir: Path,
    *,
    workspace_root: Path | None = None,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    plan_dir = Path(plan_dir).resolve()
    workspace_root = Path(workspace_root).resolve() if workspace_root is not None else plan_dir.parents[2]
    findings: list[GateFinding] = []

    actual = {path.name for path in plan_dir.iterdir()} if plan_dir.is_dir() else set()
    for missing in sorted(REQUIRED_ARTIFACTS - actual):
        findings.append(GateFinding("GATE_ARTIFACT_MISSING", missing, "Required intake artifact is missing."))
    for unexpected in sorted(actual - REQUIRED_ARTIFACTS):
        findings.append(
            GateFinding(
                "GATE_ARTIFACT_UNEXPECTED",
                unexpected,
                "Unexpected artifact exists in the canonical planning directory.",
            )
        )

    project: dict[str, Any] = {}
    project_path = plan_dir / "project.json"
    if project_path.is_file():
        try:
            loaded = json.loads(_read_text(project_path))
        except json.JSONDecodeError as exc:
            findings.append(GateFinding("GATE_PROJECT_JSON", "project.json", f"Invalid JSON: {exc}"))
        else:
            if isinstance(loaded, dict):
                project = loaded
                schema = load_schema(PROJECT_SCHEMA)
                for message in validate_json_schema(project, schema):
                    findings.append(GateFinding("GATE_PROJECT_SCHEMA", "project.json", message))
            else:
                findings.append(GateFinding("GATE_PROJECT_JSON", "project.json", "Root must be an object."))

    plan_text = _read_text(plan_dir / "PLANNING.md") if (plan_dir / "PLANNING.md").is_file() else ""
    plan_sections = _sections(plan_text)
    for heading in REQUIRED_PLAN_SECTIONS:
        if not plan_sections.get(heading, "").strip():
            findings.append(
                GateFinding("GATE_SECTION", "PLANNING.md", f"Required section {heading!r} is missing or empty.")
            )

    project_type = project.get("project_type")
    if isinstance(project_type, str) and project_type not in plan_sections.get("Project Type", ""):
        findings.append(
            GateFinding(
                "GATE_PROJECT_TYPE",
                "PLANNING.md",
                "Project Type section must match project.json.",
            )
        )

    valid_acceptance, acceptance_findings = _acceptance_findings(
        plan_sections.get("Acceptance Criteria", "")
    )
    findings.extend(acceptance_findings)

    if "creator-execution-cycle" not in plan_sections.get("Handoff Target", ""):
        findings.append(
            GateFinding(
                "GATE_HANDOFF_TARGET",
                "PLANNING.md",
                "Handoff Target must be creator-execution-cycle.",
            )
        )

    project_id = project.get("project_id")
    if isinstance(project_id, str):
        for filename in ("INTAKE-STATE.md", "HANDOFF.md"):
            path = plan_dir / filename
            if path.is_file() and project_id not in _read_text(path):
                findings.append(
                    GateFinding(
                        "GATE_PROJECT_ID",
                        filename,
                        "Artifact must preserve the canonical project ID.",
                    )
                )

    for asset in project.get("source_assets", []) if isinstance(project.get("source_assets"), list) else []:
        if not isinstance(asset, str):
            continue
        if asset.startswith("MISSING:"):
            if not asset.removeprefix("MISSING:").strip():
                findings.append(
                    GateFinding("GATE_SOURCE_ASSET", "project.json", "MISSING source marker needs a description.")
                )
            continue
        relative = Path(asset)
        if relative.is_absolute() or ".." in relative.parts or not (workspace_root / relative).is_file():
            findings.append(
                GateFinding(
                    "GATE_SOURCE_ASSET",
                    "project.json",
                    f"Source asset does not resolve or is unsafe: {asset}",
                )
            )

    questions_text = (
        _read_text(plan_dir / "OPEN-QUESTIONS.md")
        if (plan_dir / "OPEN-QUESTIONS.md").is_file()
        else ""
    )
    blocking = _question_items(questions_text, "Blocking")
    non_blocking = _question_items(questions_text, "Non-Blocking")
    if blocking:
        findings.append(
            GateFinding(
                "GATE_BLOCKING_QUESTIONS",
                "OPEN-QUESTIONS.md",
                f"{len(blocking)} blocking question(s) remain.",
            )
        )

    if findings:
        result = "fail_needs_more_planning"
    elif non_blocking:
        result = "pass_with_non_blocking_questions"
    else:
        result = "pass"

    return {
        "schema_version": "1.0.0",
        "project_id": project_id or "",
        "result": result,
        "evaluated_at": evaluated_at or _now(),
        "valid_acceptance_criteria": valid_acceptance,
        "blocking_question_count": len(blocking),
        "non_blocking_question_count": len(non_blocking),
        "findings": [asdict(item) for item in sorted(set(findings))],
    }


def record_gate_result(plan_dir: Path, report: dict[str, Any]) -> None:
    if report.get("result") not in RESULTS:
        raise PlanningGateError("invalid gate result")
    project_path = Path(plan_dir) / "project.json"
    try:
        project = json.loads(project_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanningGateError(f"cannot update project.json: {exc}") from exc
    if not isinstance(project, dict):
        raise PlanningGateError("project.json root must be an object")
    project["quality_gate_result"] = report["result"]
    project["stage"] = "planned" if report["result"] in {"pass", "pass_with_non_blocking_questions"} else "ideating"
    project["updated_at"] = report["evaluated_at"]
    atomic_write_json(project_path, project, mode=0o600)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--record", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report = evaluate_plan(args.plan_dir, workspace_root=args.workspace_root)
        if args.record:
            record_gate_result(args.plan_dir, report)
    except (PlanningGateError, OSError) as exc:
        print(f"Planning gate failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["result"] != "fail_needs_more_planning" else 1


if __name__ == "__main__":
    raise SystemExit(main())
