#!/usr/bin/env python3
"""Derive Creator Toolchain workspace health from current repository evidence."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_rule_conflicts import RuleConflictError, audit_rules
    from creator_schema_validation import validate_workspace
    from creator_state_store import load_json, safe_path, validate_surface
    from creator_transactions import atomic_write_bytes, atomic_write_json
    from json_schema_lite import load_schema, validate as validate_json_schema
    from package_integrity import check_integrity_report
    from sync_plugin_skills import synchronize as check_skill_mirror
except ImportError:
    from scripts.creator_rule_conflicts import RuleConflictError, audit_rules
    from scripts.creator_schema_validation import validate_workspace
    from scripts.creator_state_store import load_json, safe_path, validate_surface
    from scripts.creator_transactions import atomic_write_bytes, atomic_write_json
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema
    from scripts.package_integrity import check_integrity_report
    from scripts.sync_plugin_skills import synchronize as check_skill_mirror

ROOT = Path(__file__).resolve().parents[1]
HEALTH_REPORT_RELATIVE = Path(".creator/health/health-report.json")
HEALTH_SCHEMA_RELATIVE = Path("schemas/workspace/health-report.schema.json")
LEVEL_ORDER = {"green": 0, "amber": 1, "red": 2}


class HealthCheckError(RuntimeError):
    """Raised when health cannot be calculated or persisted safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _signal(signal_id: str, level: str, weight: int, path: str, message: str) -> dict[str, Any]:
    return {
        "signal_id": signal_id,
        "level": level,
        "weight": weight,
        "path": path,
        "message": message,
    }


def _project_ids(root: Path) -> set[str]:
    try:
        projects = load_json(safe_path(root, ".creator/projects.json")).get("projects", [])
    except Exception:
        return set()
    return {
        item.get("project_id")
        for item in projects
        if isinstance(item, dict) and isinstance(item.get("project_id"), str)
    }


def _plan_signals(root: Path, calculated: datetime, stale_days: int) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    plans_root = root / ".creator/plans"
    if not plans_root.is_dir():
        return signals
    for project_path in sorted(plans_root.glob("*/project.json")):
        try:
            project = json.loads(project_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            signals.append(
                _signal(
                    "PLAN_INVALID",
                    "red",
                    50,
                    project_path.relative_to(root).as_posix(),
                    str(exc),
                )
            )
            continue
        if not isinstance(project, dict):
            signals.append(
                _signal(
                    "PLAN_INVALID",
                    "red",
                    50,
                    project_path.relative_to(root).as_posix(),
                    "project.json root is not an object",
                )
            )
            continue
        stage = project.get("stage")
        updated = _parse_time(project.get("updated_at"))
        if stage in {"ideating", "planned", "graduated"} and updated is not None:
            age = (calculated - updated).days
            if age > stale_days:
                signals.append(
                    _signal(
                        "STALE_PLAN",
                        "amber",
                        10,
                        project_path.relative_to(root).as_posix(),
                        f"Plan has not been updated for {age} days.",
                    )
                )
    return signals


def _execution_signals(root: Path, registered: set[str]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    execution_root = root / ".creator/executions"
    if not execution_root.is_dir():
        return signals
    for execution_dir in sorted(path for path in execution_root.iterdir() if path.is_dir()):
        state_path = execution_dir / "execution-state.json"
        if not state_path.is_file():
            signals.append(
                _signal(
                    "ORPHAN_EXECUTION",
                    "red",
                    50,
                    execution_dir.relative_to(root).as_posix(),
                    "Execution directory has no execution-state.json.",
                )
            )
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            signals.append(
                _signal(
                    "EXECUTION_STATE_INVALID",
                    "red",
                    50,
                    state_path.relative_to(root).as_posix(),
                    str(exc),
                )
            )
            continue
        project_id = state.get("project_id") if isinstance(state, dict) else None
        if isinstance(project_id, str) and project_id not in registered:
            signals.append(
                _signal(
                    "UNREGISTERED_EXECUTION",
                    "amber",
                    15,
                    execution_dir.relative_to(root).as_posix(),
                    f"Execution project {project_id} is not registered in .creator/projects.json.",
                )
            )
        current = state.get("current_state") if isinstance(state, dict) else None
        artifacts = state.get("artifacts", {}) if isinstance(state, dict) else {}
        if current in {"DONE", "DONE_WITH_CONCERNS"}:
            for key in ("reconciliation", "summary", "state_update_proposal"):
                relative = artifacts.get(key) if isinstance(artifacts, dict) else None
                if not isinstance(relative, str) or not (execution_dir / relative).is_file():
                    signals.append(
                        _signal(
                            "MISSING_RECONCILIATION",
                            "red",
                            50,
                            state_path.relative_to(root).as_posix(),
                            f"Terminal execution is missing {key}.",
                        )
                    )
    return signals


def _rule_conflict_signals(
    root: Path,
    audited_at: str,
    schema_root: Path,
) -> list[dict[str, Any]]:
    """Convert the live Rule audit into Health signals.

    The conflict report is derived from the current Rule bytes. A stored conflict
    report is useful evidence, but it is never trusted instead of a live audit.
    """

    try:
        report = audit_rules(root, audited_at=audited_at, schema_root=schema_root)
    except (RuleConflictError, OSError, ValueError) as exc:
        return [
            _signal(
                "RULE_CONFLICT_AUDIT_FAILURE",
                "red",
                50,
                ".creator/rules.json",
                f"Rule conflict audit failed: {exc}",
            )
        ]

    signals: list[dict[str, Any]] = []
    for conflict in report["conflicts"]:
        blocking = bool(conflict["blocking"])
        conflict_id = str(conflict["conflict_id"])
        conflict_type = str(conflict["conflict_type"])
        message = str(conflict["message"])
        domains = ", ".join(conflict.get("domains", [])) or "unscoped"
        signals.append(
            _signal(
                "RULE_CONFLICT_BLOCKING" if blocking else "RULE_CONFLICT_ADVISORY",
                "red" if blocking else "amber",
                50 if blocking else 10,
                ".creator/rules.json",
                f"{conflict_id} [{conflict_type}; domains={domains}]: {message}",
            )
        )
    return signals


def _repository_signals(root: Path) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    behavior_path = root / "docs/qa/behavior-acceptance-status.json"
    if not behavior_path.is_file():
        signals.append(
            _signal(
                "BEHAVIOR_STATUS_MISSING",
                "red",
                50,
                "docs/qa/behavior-acceptance-status.json",
                "Behavior evidence freshness status is missing.",
            )
        )
    else:
        try:
            behavior = json.loads(behavior_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            signals.append(
                _signal(
                    "BEHAVIOR_STATUS_INVALID",
                    "red",
                    50,
                    behavior_path.relative_to(root).as_posix(),
                    str(exc),
                )
            )
        else:
            status = behavior.get("status") if isinstance(behavior, dict) else None
            if status == "STALE":
                signals.append(
                    _signal(
                        "BEHAVIOR_EVIDENCE_STALE",
                        "amber",
                        20,
                        behavior_path.relative_to(root).as_posix(),
                        str(behavior.get("reason") or "Behavior evidence is stale."),
                    )
                )
            elif status not in {"CURRENT", "PASS"}:
                signals.append(
                    _signal(
                        "BEHAVIOR_STATUS_INVALID",
                        "red",
                        50,
                        behavior_path.relative_to(root).as_posix(),
                        f"Unsupported behavior status: {status!r}.",
                    )
                )
    for finding in check_skill_mirror(
        root / ".agents/skills",
        root / "plugin/creator-toolchain/skills",
        write=False,
    ):
        signals.append(
            _signal(
                "MIRROR_MISMATCH",
                "red",
                50,
                "plugin/creator-toolchain/skills",
                finding,
            )
        )
    report_path = root / "docs/qa/package-integrity-report.json"
    if not report_path.is_file():
        signals.append(
            _signal(
                "PACKAGE_REPORT_MISSING",
                "red",
                50,
                report_path.relative_to(root).as_posix(),
                "Package integrity report is missing.",
            )
        )
    else:
        for finding in check_integrity_report(
            root,
            root / "plugin/creator-toolchain",
            report_path,
        ):
            signals.append(
                _signal(
                    "PACKAGE_INTEGRITY_FAILURE",
                    "red",
                    50,
                    report_path.relative_to(root).as_posix(),
                    finding,
                )
            )
    return signals


def calculate_health(
    root: Path,
    *,
    calculated_at: str | None = None,
    stale_plan_days: int = 30,
    include_repository_checks: bool = True,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    calculated_at = calculated_at or _now()
    calculated = _parse_time(calculated_at)
    if calculated is None:
        raise HealthCheckError("calculated_at must be ISO-8601")

    signals: list[dict[str, Any]] = []
    for finding in validate_workspace(root, schema_root=schema_root):
        signals.append(_signal("WORKSPACE_CONTRACT_FAILURE", "red", 50, ".creator", finding))
    signals.extend(_plan_signals(root, calculated, stale_plan_days))
    signals.extend(_execution_signals(root, _project_ids(root)))
    signals.extend(_rule_conflict_signals(root, calculated_at, schema_root))
    if include_repository_checks:
        signals.extend(_repository_signals(root))

    signals = sorted(
        signals,
        key=lambda item: (
            LEVEL_ORDER[item["level"]],
            item["signal_id"],
            item["path"],
            item["message"],
        ),
    )
    counts = {
        "amber": sum(item["level"] == "amber" for item in signals),
        "red": sum(item["level"] == "red" for item in signals),
    }
    score = sum(int(item["weight"]) for item in signals)
    level = "red" if counts["red"] else "amber" if counts["amber"] else "green"
    next_action = (
        "Resolve the first red health signal, then rerun the health check."
        if level == "red"
        else "Resolve the first amber health signal before release."
        if level == "amber"
        else "No corrective action is required."
    )
    report = {
        "schema_version": "1.0.0",
        "calculated_at": calculated_at,
        "score": score,
        "level": level,
        "summary": f"Derived {counts['red']} red and {counts['amber']} amber signal(s); score={score}.",
        "recommended_next_action": next_action,
        "counts": counts,
        "signals": signals,
    }
    findings = validate_json_schema(
        report,
        load_schema(schema_root / HEALTH_SCHEMA_RELATIVE),
    )
    if findings:
        raise HealthCheckError("health report failed schema validation: " + "; ".join(findings))
    return report


def write_health(
    root: Path,
    report: dict[str, Any],
    *,
    schema_root: Path = ROOT,
) -> None:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    report_path = safe_path(root, HEALTH_REPORT_RELATIVE)
    state_path = safe_path(root, ".creator/state.json")
    report_before = report_path.read_bytes() if report_path.is_file() else None
    state_before = state_path.read_bytes()
    state = load_json(state_path)
    state["last_health_check"] = report["calculated_at"]
    state["updated_at"] = report["calculated_at"]
    state["state_divergence"] = {
        "score": report["score"],
        "level": report["level"],
        "notes": f"{report['summary']} Evidence: {HEALTH_REPORT_RELATIVE.as_posix()}.",
    }
    findings = validate_surface(".creator/state.json", state, schema_root=schema_root)
    if findings:
        raise HealthCheckError("state update failed validation: " + "; ".join(findings))
    try:
        atomic_write_json(report_path, report, mode=0o600)
        atomic_write_json(state_path, state, mode=0o600)
        workspace_findings = validate_workspace(root, schema_root=schema_root)
        if workspace_findings:
            raise HealthCheckError(
                "post-write workspace validation failed: " + "; ".join(workspace_findings)
            )
    except Exception:
        atomic_write_bytes(state_path, state_before, mode=0o600)
        if report_before is None:
            if report_path.exists():
                report_path.unlink()
        else:
            atomic_write_bytes(report_path, report_before, mode=0o600)
        raise


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--calculated-at")
    parser.add_argument("--stale-plan-days", type=int, default=30)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--fail-on", choices=("never", "red", "amber"), default="red")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report = calculate_health(
            args.root,
            calculated_at=args.calculated_at,
            stale_plan_days=args.stale_plan_days,
        )
        if args.write:
            write_health(args.root, report)
        text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    except (HealthCheckError, OSError, ValueError) as exc:
        print(f"Creator health check failed: {exc}", file=sys.stderr)
        return 2
    if args.fail_on == "amber" and report["level"] in {"amber", "red"}:
        return 1
    if args.fail_on == "red" and report["level"] == "red":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
