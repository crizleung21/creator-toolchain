#!/usr/bin/env python3
"""Run the writable Creator Toolchain golden workflow in an isolated workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from bootstrap_creator_workspace import bootstrap
    from creator_evidence_audit import create_execution_handoff, issue_finding, plan_remediation
    from creator_execution_closure import close_execution
    from creator_execution_lifecycle import initialize_execution, record_verification, transition_execution, transition_task
    from creator_health_check import calculate_health, write_health
    from creator_intake_artifacts import create_intake_package
    from creator_intake_workflow import approve_intake, handoff_intake, inspect_registration_proposal
    from creator_rule_store import preflight
    from creator_schema_validation import validate_workspace
    from creator_transactions import atomic_write_bytes
    from json_schema_lite import load_schema, validate as validate_json_schema
    from reconcile_creator_state import apply_reconciliation
except ImportError:
    from scripts.bootstrap_creator_workspace import bootstrap
    from scripts.creator_evidence_audit import create_execution_handoff, issue_finding, plan_remediation
    from scripts.creator_execution_closure import close_execution
    from scripts.creator_execution_lifecycle import initialize_execution, record_verification, transition_execution, transition_task
    from scripts.creator_health_check import calculate_health, write_health
    from scripts.creator_intake_artifacts import create_intake_package
    from scripts.creator_intake_workflow import approve_intake, handoff_intake, inspect_registration_proposal
    from scripts.creator_rule_store import preflight
    from scripts.creator_schema_validation import validate_workspace
    from scripts.creator_transactions import atomic_write_bytes
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema
    from scripts.reconcile_creator_state import apply_reconciliation

ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA = Path("schemas/qa/golden-e2e-report.schema.json")
FIXTURE_ID = "creator-asset-naming-checker"
TIMESTAMPS = [
    "2026-07-23T12:30:00Z", "2026-07-23T12:31:00Z", "2026-07-23T12:32:00Z",
    "2026-07-23T12:33:00Z", "2026-07-23T12:34:00Z", "2026-07-23T12:35:00Z",
    "2026-07-23T12:36:00Z", "2026-07-23T12:37:00Z", "2026-07-23T12:38:00Z",
    "2026-07-23T12:39:00Z", "2026-07-23T12:40:00Z", "2026-07-23T12:41:00Z",
    "2026-07-23T12:42:00Z", "2026-07-23T12:43:00Z", "2026-07-23T12:44:00Z",
    "2026-07-23T12:45:00Z", "2026-07-23T12:46:00Z", "2026-07-23T12:47:00Z",
]


class GoldenE2EError(RuntimeError):
    """Raised when the writable golden workflow cannot prove its result."""


UTILITY_SOURCE = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

VALID_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.[a-z0-9]+$")


def build_report(names: list[str]) -> dict[str, object]:
    counts = Counter(names)
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    invalid = sorted(name for name in names if VALID_NAME.fullmatch(name) is None)
    return {
        "schema_version": "1.0.0",
        "duplicates": duplicates,
        "invalid_names": invalid,
        "input_count": len(names),
        "valid": not duplicates and not invalid,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = json.loads(args.input.read_text(encoding="utf-8"))
    names = value.get("names")
    if not isinstance(names, list) or not all(isinstance(item, str) for item in names):
        raise SystemExit("manifest names must be an array of strings")
    report = build_report(names)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _commit_sha(source_root: Path, override: str | None) -> str:
    value = (override or os.environ.get("GITHUB_SHA", "")).strip().lower()
    if not value:
        process = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source_root, text=True, capture_output=True, check=False)
        if process.returncode == 0:
            value = process.stdout.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise GoldenE2EError("source commit SHA must be a 40-character hexadecimal value")
    return value


def _package_payload(source_root: Path) -> str:
    path = source_root / "docs/qa/package-integrity-report.json"
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GoldenE2EError(f"cannot load package integrity report: {exc}") from exc
    payload = report.get("payload_sha256") if isinstance(report, dict) else None
    if not isinstance(payload, str) or not re.fullmatch(r"[0-9a-f]{64}", payload):
        raise GoldenE2EError("package payload SHA-256 is invalid")
    return payload


def _step(steps: list[dict[str, Any]], name: str, *evidence: str) -> None:
    steps.append({"step": name, "status": "PASS", "evidence": list(evidence)})


def _write_fixture_utility(workspace: Path) -> tuple[Path, Path, Path]:
    source = workspace / "src/creator_asset_naming_checker.py"
    manifest = workspace / "fixtures/asset-manifest.json"
    first = workspace / "evidence/naming-report.json"
    source.parent.mkdir(parents=True)
    manifest.parent.mkdir(parents=True)
    first.parent.mkdir(parents=True)
    source.write_text(UTILITY_SOURCE, encoding="utf-8")
    manifest.write_text(json.dumps({"names": ["hero-shot.png", "hero-shot.png", "scene-01.mp4", "Hero Shot.png", "bad name?.png"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return source, manifest, first


def _run_utility(workspace: Path, source: Path, manifest: Path, first: Path) -> tuple[dict[str, Any], str]:
    second = workspace / "evidence/naming-report-repeat.json"
    command = [sys.executable, source.relative_to(workspace).as_posix(), "--input", manifest.relative_to(workspace).as_posix(), "--output", first.relative_to(workspace).as_posix()]
    first_run = subprocess.run(command, cwd=workspace, text=True, capture_output=True, check=False)
    if first_run.returncode != 0:
        raise GoldenE2EError(f"utility first run failed: {first_run.stderr.strip()}")
    command[-1] = second.relative_to(workspace).as_posix()
    second_run = subprocess.run(command, cwd=workspace, text=True, capture_output=True, check=False)
    if second_run.returncode != 0:
        raise GoldenE2EError(f"utility second run failed: {second_run.stderr.strip()}")
    if first.read_bytes() != second.read_bytes():
        raise GoldenE2EError("utility output is not byte-deterministic")
    report = json.loads(first.read_text(encoding="utf-8"))
    if report.get("duplicates") != ["hero-shot.png"]:
        raise GoldenE2EError("utility did not report the expected duplicate")
    if len(report.get("invalid_names", [])) < 2:
        raise GoldenE2EError("utility did not report the expected invalid names")
    return report, _sha(first)


def run_golden_e2e(workspace: Path, *, source_root: Path = ROOT, commit_sha: str | None = None, report_path: Path | None = None) -> dict[str, Any]:
    """Run the complete writable fixture and return a portable evidence report."""
    workspace = Path(workspace).resolve()
    source_root = Path(source_root).resolve()
    if workspace.exists() and any(workspace.iterdir()):
        raise GoldenE2EError("golden workspace must be empty")
    workspace.mkdir(parents=True, exist_ok=True)
    commit = _commit_sha(source_root, commit_sha)
    package_payload = _package_payload(source_root)
    steps: list[dict[str, Any]] = []
    bootstrap(workspace, workspace_id="golden-e2e", display_name="Golden E2E", write=True)
    for relative in (".creator/rules.json", ".creator/decisions.json"):
        atomic_write_bytes(workspace / relative, (source_root / relative).read_bytes(), mode=0o600)
    _step(steps, "bootstrap", ".creator/workspace.json", ".creator/rules.json")
    request = {"title": "Creator Asset Naming Checker", "project_type": "utility", "goal": "Create a deterministic manifest naming checker.", "context": "Creator pipelines need repeatable duplicate and invalid-name findings.", "scope": ["Manifest input", "Deterministic JSON validation report"], "out_of_scope": ["Automatic renaming", "Asset deletion"], "acceptance_criteria": [{"id": "AC-1", "title": "Duplicates", "given": "a manifest with duplicate names", "when": "the checker runs", "then": "each duplicate name is listed"}, {"id": "AC-2", "title": "Invalid names", "given": "a manifest with unsafe names", "when": "the checker runs", "then": "each invalid name is listed"}, {"id": "AC-3", "title": "Repeatability", "given": "the same manifest", "when": "the checker runs twice", "then": "both report files are byte-identical"}], "risks": ["Unsafe paths", "Nondeterministic ordering"]}
    intake = create_intake_package(workspace, request, timestamp=TIMESTAMPS[0], registry_root=source_root)
    plan_dir = Path(intake["plan_dir"])
    project = json.loads((plan_dir / "project.json").read_text(encoding="utf-8"))
    project_id = project["project_id"]
    _step(steps, "intake", f".creator/plans/{intake['slug']}/project.json", f".creator/plans/{intake['slug']}/PLANNING.md")
    approve_intake(workspace, intake["slug"], actor="golden-e2e", decision="handoff-to-execution", timestamp=TIMESTAMPS[1])
    registration = inspect_registration_proposal(workspace, intake["slug"])
    apply_reconciliation(workspace, registration["proposal_path"], actor="golden-e2e", timestamp=TIMESTAMPS[2], schema_root=source_root, include_repository_checks=False)
    _step(steps, "approve-and-register", registration["proposal_path"], f".creator/reconciliation/{registration['proposal_id']}.json")
    handoff = handoff_intake(workspace, intake["slug"], timestamp=TIMESTAMPS[3])
    handoff_path = Path(handoff["execution_handoff_path"])
    handoff_relative = handoff_path.relative_to(workspace).as_posix() if handoff_path.is_absolute() else handoff_path.as_posix()
    _step(steps, "execution-handoff", handoff_relative)
    tasks = [{"title": "Implement deterministic asset naming checker", "acceptance_criteria": ["Given duplicate and invalid manifest entries, when the checker runs twice, then both reports are byte-identical and contain the expected findings."], "affected_files": ["src/creator_asset_naming_checker.py", "fixtures/asset-manifest.json", "evidence/naming-report.json"], "verification": {"method": "command", "command": "python3 src/creator_asset_naming_checker.py --input fixtures/asset-manifest.json --output evidence/naming-report.json", "expected_result": "Exit code 0, expected findings, and byte-identical repeated output."}}]
    initialize_execution(workspace, handoff_relative, tasks, timestamp=TIMESTAMPS[4], schema_root=source_root)
    execution_dir = workspace / ".creator/executions" / project_id
    task_document = json.loads((execution_dir / "tasks.json").read_text(encoding="utf-8"))
    task_id = task_document["tasks"][0]["task_id"]
    transition_execution(workspace, project_id, "EXECUTING", actor="golden-e2e", reason="Begin the approved fixture task.", timestamp=TIMESTAMPS[5], schema_root=source_root)
    transition_task(workspace, project_id, task_id, "EXECUTING", actor="golden-e2e", reason="Create the deterministic utility.", timestamp=TIMESTAMPS[6], schema_root=source_root)
    source, manifest, utility_report_path = _write_fixture_utility(workspace)
    utility_report, utility_sha = _run_utility(workspace, source, manifest, utility_report_path)
    transition_task(workspace, project_id, task_id, "EXECUTED", actor="golden-e2e", reason="Utility and deterministic report were created.", timestamp=TIMESTAMPS[7], schema_root=source_root)
    transition_execution(workspace, project_id, "VERIFYING", actor="golden-e2e", reason="Verify the utility evidence.", timestamp=TIMESTAMPS[8], schema_root=source_root)
    record_verification(workspace, project_id, task_id, result="PASS", actual_result="Utility exited 0 and repeated output was byte-identical.", evidence_relative="evidence/naming-report.json", timestamp=TIMESTAMPS[9], schema_root=source_root)
    _step(steps, "execute-and-verify", "src/creator_asset_naming_checker.py", "evidence/naming-report.json")
    transition_execution(workspace, project_id, "RECONCILING", actor="golden-e2e", reason="All accepted tasks have current verification evidence.", timestamp=TIMESTAMPS[10], schema_root=source_root)
    close_execution(workspace, project_id, status="DONE", actor="golden-e2e", recommended_next_action="Apply the staged execution state proposal.", timestamp=TIMESTAMPS[11], schema_root=source_root)
    update_proposal = f".creator/executions/{project_id}/state-update-proposal.json"
    apply_reconciliation(workspace, update_proposal, actor="golden-e2e", timestamp=TIMESTAMPS[12], schema_root=source_root, include_repository_checks=False)
    _step(steps, "close-and-reconcile", f".creator/executions/{project_id}/RECONCILIATION-001.json", f".creator/executions/{project_id}/SUMMARY-001.md", update_proposal)
    rule_result = preflight(workspace, "Use zh-Hant to validate the creator-toolchain plugin package safely.", max_rules=8, audited_at=TIMESTAMPS[13], schema_root=source_root)
    matched_domains = sorted(item["domain_id"] for item in rule_result["matched_domains"])
    selected_rules = sorted(item["rule_id"] for item in rule_result["selected_rules"])
    if "zh-hant" not in matched_domains or "creator-toolchain" not in matched_domains:
        raise GoldenE2EError("rule preflight did not match required domains")
    _step(steps, "rule-preflight", ".creator/rules.json")
    audit_evidence = workspace / "evidence/behavior-acceptance-status.json"
    audit_evidence.write_bytes((source_root / "docs/qa/behavior-acceptance-status.json").read_bytes())
    audit_id = "AUDIT-GOLDEN-E2E"
    finding = issue_finding(workspace, audit_id, title="Behavior acceptance evidence requires a current runtime rerun", observation="The copied behavior status explicitly marks the canonical report stale.", interpretation="The runtime and writable workflow can be validated, but the stable release gate remains open.", judgment="Run all 34 behavior cases before claiming release readiness.", severity="high", confidence=0.99, evidence_quality="direct", evidence_paths=["evidence/behavior-acceptance-status.json"], disagreements=[], disagreement_state="none", limitations=["This fixture does not invoke an external Codex runtime."], actor="golden-e2e", issued_at=TIMESTAMPS[14], schema_root=source_root)
    remediation = plan_remediation(workspace, audit_id, finding["finding_id"], remediation_type="workflow", intervention_level="planning", blast_radius="medium", coupling_risk="medium", regression_risk="medium", confidence=0.95, verification_gate="All 34 behavior cases pass with evidence-bound observation spans.", rollback_criteria="Retain the previous report and mark the failed rerun as authoritative evidence.", recommended_action="Execute the Phase 7 behavior harness with current runtime adapters.", actor="golden-e2e", created_at=TIMESTAMPS[15], schema_root=source_root)
    audit_handoff = create_execution_handoff(workspace, audit_id, finding_ids=[finding["finding_id"]], task_ids=[remediation["task_id"]], dependency_graph=[], risks=["Behavior semantics can regress even when static contracts pass."], verification_gates=["All 34 cases run.", "Every required observation has a response evidence span."], rollback_criteria=["Do not replace a current report with an incomplete run."], authorization_status="planned", actor=None, generated_at=TIMESTAMPS[16], schema_root=source_root)
    _step(steps, "evidence-audit", f".creator/audits/{audit_id}/findings/{finding['finding_id']}.json", f".creator/audits/{audit_id}/handoffs/{audit_handoff['handoff_id']}.json")
    health = calculate_health(workspace, calculated_at=TIMESTAMPS[17], include_repository_checks=False, schema_root=source_root)
    write_health(workspace, health, schema_root=source_root)
    findings = validate_workspace(workspace, schema_root=source_root)
    if findings:
        raise GoldenE2EError("final workspace validation failed: " + "; ".join(findings))
    if health["level"] != "green" or health["score"] != 0 or health["signals"]:
        raise GoldenE2EError(f"final workspace health is not green: {health}")
    projects = json.loads((workspace / ".creator/projects.json").read_text(encoding="utf-8"))
    registered = next((item for item in projects["projects"] if item["project_id"] == project_id), None)
    if not registered or registered.get("status") != "done":
        raise GoldenE2EError("project state was not reconciled to done")
    _step(steps, "final-validation", ".creator/health/health-report.json", ".creator/projects.json")
    artifacts = sorted({item for step in steps for item in step["evidence"]} | {f".creator/audits/{audit_id}/remediation/{remediation['task_id']}.json", "evidence/behavior-acceptance-status.json", "fixtures/asset-manifest.json"})
    report = {"schema_version": "1.0.0", "status": "PASS", "fixture_id": FIXTURE_ID, "source_commit_sha": commit, "package_payload_sha256": package_payload, "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", "started_at": TIMESTAMPS[0], "finished_at": TIMESTAMPS[17], "workspace_root": ".", "project_id": project_id, "steps": steps, "utility": {"report_path": "evidence/naming-report.json", "report_sha256": utility_sha, "duplicate_count": len(utility_report["duplicates"]), "invalid_count": len(utility_report["invalid_names"]), "deterministic": True}, "rule_preflight": {"matched_domains": matched_domains, "selected_rules": selected_rules}, "audit": {"audit_id": audit_id, "finding_id": finding["finding_id"], "task_id": remediation["task_id"], "handoff_id": audit_handoff["handoff_id"]}, "final_health": {"level": health["level"], "score": health["score"], "signal_count": len(health["signals"])}, "final_validation_findings": findings, "artifacts": artifacts, "recommended_next_action": "Run all 34 behavior cases with current response and evaluator adapters."}
    schema_findings = validate_json_schema(report, load_schema(source_root / REPORT_SCHEMA))
    if schema_findings:
        raise GoldenE2EError("golden report failed schema validation: " + "; ".join(schema_findings))
    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--commit-sha")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_golden_e2e(args.root, source_root=args.source_root, commit_sha=args.commit_sha, report_path=args.report)
    except (GoldenE2EError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Golden E2E failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
