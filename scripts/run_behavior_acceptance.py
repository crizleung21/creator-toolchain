#!/usr/bin/env python3
"""Run Creator Toolchain behavior cases through pluggable response and evaluation adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from evaluate_behavior_observations import ObservationEvaluationError, evaluate_case
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:
    from scripts.evaluate_behavior_observations import ObservationEvaluationError, evaluate_case
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
HARNESS_VERSION = "1.0.0"
CATALOG_RELATIVE = Path("docs/qa/behavior-acceptance-cases.json")
PACKAGE_REPORT_RELATIVE = Path("docs/qa/package-integrity-report.json")
RUN_SCHEMA_RELATIVE = Path("schemas/qa/behavior-run.schema.json")
REPORT_SCHEMA_RELATIVE = Path("schemas/qa/behavior-report.schema.json")
SKILLS = {"creator-orchestrator", "creator-intake-planner", "creator-execution-cycle", "creator-workspace-manager", "creator-rule-router", "creator-skill-workbench", "creator-evidence-audit"}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class BehaviorAcceptanceError(RuntimeError):
    """Raised when the behavior harness cannot produce trustworthy evidence."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BehaviorAcceptanceError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BehaviorAcceptanceError(f"JSON root must be an object: {path}")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    if catalog.get("schema_version") != "1.0.0":
        raise BehaviorAcceptanceError("behavior catalog schema_version must be 1.0.0")
    cases = catalog.get("cases")
    if not isinstance(cases, list) or not cases:
        raise BehaviorAcceptanceError("behavior catalog cases must be a non-empty array")
    if catalog.get("case_count") != len(cases):
        raise BehaviorAcceptanceError("behavior catalog case_count does not match cases")
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise BehaviorAcceptanceError(f"cases[{index}] must be an object")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not SAFE_ID_RE.fullmatch(case_id):
            raise BehaviorAcceptanceError(f"cases[{index}].case_id is invalid")
        if case_id in seen:
            raise BehaviorAcceptanceError(f"duplicate behavior case_id: {case_id}")
        seen.add(case_id)
        source_mode = case.get("source_mode")
        if source_mode not in {"plugin-only", "repo-local"}:
            raise BehaviorAcceptanceError(f"{case_id}.source_mode is invalid")
        expected_skill = case.get("expected_skill")
        if expected_skill not in SKILLS:
            raise BehaviorAcceptanceError(f"{case_id}.expected_skill is invalid")
        prompt = case.get("prompt")
        required = case.get("required_observations")
        prohibited = case.get("prohibited_observations")
        if not isinstance(prompt, str) or not prompt.strip():
            raise BehaviorAcceptanceError(f"{case_id}.prompt must be non-empty")
        if not isinstance(required, list) or not required or not all(isinstance(item, str) and item.strip() for item in required):
            raise BehaviorAcceptanceError(f"{case_id}.required_observations is invalid")
        if not isinstance(prohibited, list) or not prohibited or not all(isinstance(item, str) and item.strip() for item in prohibited):
            raise BehaviorAcceptanceError(f"{case_id}.prohibited_observations is invalid")
        normalized.append({"case_id": case_id, "source_mode": source_mode, "prompt": prompt.strip(), "expected_skill": expected_skill, "required_observations": [item.strip() for item in required], "prohibited_observations": [item.strip() for item in prohibited]})
    return normalized


def _git_commit(root: Path, override: str | None) -> str:
    if override:
        value = override.strip().lower()
    else:
        value = os.environ.get("GITHUB_SHA", "").strip().lower()
        if not value:
            process = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False)
            if process.returncode == 0:
                value = process.stdout.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise BehaviorAcceptanceError("commit SHA is unavailable; pass --commit-sha with a 40-character hexadecimal SHA")
    return value


def _package_payload(root: Path, package_report: Path) -> str:
    report = _load_json(root / package_report)
    payload = report.get("payload_sha256")
    if not isinstance(payload, str) or not re.fullmatch(r"[0-9a-f]{64}", payload):
        raise BehaviorAcceptanceError("package report payload_sha256 is invalid")
    return payload


def _safe_relative(value: str | Path, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise BehaviorAcceptanceError(f"{label} must be repository-relative")
    return path


def _run_json_command(command: str, payload: dict[str, Any], *, cwd: Path, timeout: int) -> tuple[dict[str, Any], int, str]:
    argv = shlex.split(command)
    if not argv:
        raise BehaviorAcceptanceError("adapter command must not be empty")
    process = subprocess.run(argv, cwd=cwd, input=json.dumps(payload, ensure_ascii=False), text=True, capture_output=True, timeout=timeout, check=False)
    if process.returncode != 0:
        raise BehaviorAcceptanceError(f"adapter exited {process.returncode}: {process.stderr.strip()}")
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise BehaviorAcceptanceError(f"adapter did not return one JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise BehaviorAcceptanceError("adapter JSON root must be an object")
    return value, process.returncode, process.stderr


def _validate_schema(value: dict[str, Any], schema: Path, schema_root: Path) -> None:
    findings = validate_json_schema(value, load_schema(schema_root / schema))
    if findings:
        raise BehaviorAcceptanceError(f"{schema.name} validation failed: " + "; ".join(findings))


def assess_report_freshness(report: dict[str, Any], *, commit_sha: str, package_payload_sha256: str, catalog_sha256: str, harness_version: str = HARNESS_VERSION) -> dict[str, Any]:
    mismatches = []
    expected = {"commit_sha": commit_sha, "package_payload_sha256": package_payload_sha256, "catalog_sha256": catalog_sha256, "harness_version": harness_version}
    for field, current in expected.items():
        if report.get(field) != current:
            mismatches.append({"field": field, "report": report.get(field), "current": current})
    return {"status": "CURRENT" if not mismatches else "STALE", "mismatches": mismatches}


def run_behavior_acceptance(root: Path, *, response_command: str, evaluator_command: str, run_id: str, commit_sha: str | None = None, case_ids: list[str] | None = None, catalog_relative: Path = CATALOG_RELATIVE, package_report_relative: Path = PACKAGE_REPORT_RELATIVE, output_relative: Path | None = None, timeout: int = 120, timestamp_factory: Callable[[], str] = _now, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    if not SAFE_ID_RE.fullmatch(run_id):
        raise BehaviorAcceptanceError("run_id contains unsafe characters")
    catalog_relative = _safe_relative(catalog_relative, "catalog path")
    package_report_relative = _safe_relative(package_report_relative, "package report path")
    catalog_path = root / catalog_relative
    catalog = _load_json(catalog_path)
    cases = validate_catalog(catalog)
    catalog_sha = _sha256_file(catalog_path)
    selected_ids = set(case_ids or [])
    unknown = sorted(selected_ids - {case["case_id"] for case in cases})
    if unknown:
        raise BehaviorAcceptanceError(f"unknown behavior case IDs: {unknown}")
    selected_cases = [case for case in cases if not selected_ids or case["case_id"] in selected_ids]
    output_relative = output_relative or Path(f".creator/qa/behavior-runs/{run_id}")
    output_relative = _safe_relative(output_relative, "output path")
    output_root = root / output_relative
    if output_root.exists():
        raise BehaviorAcceptanceError(f"behavior run already exists: {output_relative}")
    response_root = output_root / "responses"
    case_root = output_root / "cases"
    response_root.mkdir(parents=True)
    case_root.mkdir(parents=True)
    commit = _git_commit(root, commit_sha)
    package_payload = _package_payload(root, package_report_relative)
    run_records: list[dict[str, Any]] = []
    for case in selected_cases:
        started_at = timestamp_factory()
        raw_relative = (output_relative / "responses" / f"{case['case_id']}.txt").as_posix()
        raw_path = root / raw_relative
        try:
            response, exit_code, _ = _run_json_command(response_command, {"schema_version": "1.0.0", "case": case, "repository_root": ".", "plugin_root": "plugin/creator-toolchain", "harness_version": HARNESS_VERSION}, cwd=root, timeout=timeout)
            selected_skill = response.get("selected_skill")
            response_text = response.get("response_text")
            codex_version = response.get("codex_version")
            model_version = response.get("model_version")
            for field, value in (("selected_skill", selected_skill), ("response_text", response_text), ("codex_version", codex_version), ("model_version", model_version)):
                if not isinstance(value, str) or not value.strip():
                    raise BehaviorAcceptanceError(f"response adapter field {field} must be non-empty")
            raw_path.write_text(response_text, encoding="utf-8")
            evaluation, _, _ = _run_json_command(evaluator_command, {"schema_version": "1.0.0", "case": case, "selected_skill": selected_skill, "response_text": response_text, "raw_response_path": raw_relative, "harness_version": HARNESS_VERSION}, cwd=root, timeout=timeout)
            normalized = evaluate_case(case, response_text, selected_skill, evaluation)
            finished_at = timestamp_factory()
            record = {"schema_version": "1.0.0", "case_id": case["case_id"], "commit_sha": commit, "package_payload_sha256": package_payload, "catalog_sha256": catalog_sha, "codex_version": codex_version.strip(), "model_version": model_version.strip(), "harness_version": HARNESS_VERSION, "source_mode": case["source_mode"], "prompt": case["prompt"], "expected_skill": case["expected_skill"], "selected_skill": normalized["selected_skill"], "raw_response_path": raw_relative, "raw_response_sha256": _sha256_file(raw_path), "evaluator": normalized["evaluator"], "evaluator_version": normalized["evaluator_version"], "required_observations": normalized["required_observations"], "prohibited_observations": normalized["prohibited_observations"], "result": normalized["result"], "started_at": started_at, "finished_at": finished_at, "exit_code": exit_code}
        except (BehaviorAcceptanceError, ObservationEvaluationError, OSError, subprocess.TimeoutExpired, ValueError) as exc:
            finished_at = timestamp_factory()
            if not raw_path.exists():
                raw_path.write_text("", encoding="utf-8")
            record = {"schema_version": "1.0.0", "case_id": case["case_id"], "commit_sha": commit, "package_payload_sha256": package_payload, "catalog_sha256": catalog_sha, "codex_version": "unknown", "model_version": "unknown", "harness_version": HARNESS_VERSION, "source_mode": case["source_mode"], "prompt": case["prompt"], "expected_skill": case["expected_skill"], "selected_skill": "unknown", "raw_response_path": raw_relative, "raw_response_sha256": _sha256_file(raw_path), "evaluator": "not-run", "evaluator_version": "unknown", "required_observations": [{"observation": observation, "result": "FAIL", "evidence_excerpt": "", "response_line_start": None, "response_line_end": None, "confidence": 0.0} for observation in case["required_observations"]], "prohibited_observations": [{"observation": observation, "result": "ABSENT", "evidence_excerpt": "", "response_line_start": None, "response_line_end": None, "confidence": 0.0} for observation in case["prohibited_observations"]], "result": "ERROR", "started_at": started_at, "finished_at": finished_at, "exit_code": 2, "error": str(exc)}
        _validate_schema(record, RUN_SCHEMA_RELATIVE, schema_root)
        (case_root / f"{case['case_id']}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        run_records.append(record)
    passed = sum(item["result"] == "PASS" for item in run_records)
    failed = sum(item["result"] == "FAIL" for item in run_records)
    errored = sum(item["result"] == "ERROR" for item in run_records)
    all_cases = len(run_records) == len(cases)
    status = "ERROR" if errored else "FAIL" if failed else "PASS" if all_cases else "INCOMPLETE"
    report = {"schema_version": "1.0.0", "status": status, "run_id": run_id, "catalog_case_count": len(cases), "case_count": len(run_records), "passed": passed, "failed": failed, "errored": errored, "all_catalog_cases_run": all_cases, "commit_sha": commit, "package_payload_sha256": package_payload, "catalog_sha256": catalog_sha, "harness_version": HARNESS_VERSION, "runtime_adapter": response_command, "evaluator_adapter": evaluator_command, "generated_at": timestamp_factory(), "recommended_next_action": "Promote this report only after verifying every evidence span and current package hash." if status == "PASS" else "Resolve the first failed or errored case and rerun the complete catalog." if status in {"FAIL", "ERROR"} else "Run the remaining catalog cases; a partial report cannot satisfy the release gate.", "cases": run_records}
    _validate_schema(report, REPORT_SCHEMA_RELATIVE, schema_root)
    (output_root / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--catalog", type=Path, default=CATALOG_RELATIVE)
    parser.add_argument("--package-report", type=Path, default=PACKAGE_REPORT_RELATIVE)
    parser.add_argument("--validate-catalog", action="store_true")
    parser.add_argument("--response-command")
    parser.add_argument("--evaluator-command")
    parser.add_argument("--run-id")
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--commit-sha")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)
    try:
        catalog = _load_json(args.root.resolve() / _safe_relative(args.catalog, "catalog path"))
        cases = validate_catalog(catalog)
        if args.validate_catalog:
            print(json.dumps({"schema_version": "1.0.0", "status": "PASS", "case_count": len(cases), "catalog_sha256": _sha256_file(args.root.resolve() / args.catalog)}, indent=2, sort_keys=True))
            return 0
        if not args.response_command or not args.evaluator_command:
            raise BehaviorAcceptanceError("--response-command and --evaluator-command are required for a run")
        run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report = run_behavior_acceptance(args.root, response_command=args.response_command, evaluator_command=args.evaluator_command, run_id=run_id, commit_sha=args.commit_sha, case_ids=args.case_id, catalog_relative=args.catalog, package_report_relative=args.package_report, output_relative=args.output, timeout=args.timeout)
    except (BehaviorAcceptanceError, OSError, ValueError) as exc:
        print(f"Behavior acceptance failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
