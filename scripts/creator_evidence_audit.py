#!/usr/bin/env python3
"""Issue immutable audit findings, remediation plans, corrections, and execution handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from creator_ids import deterministic_id
    from creator_state_store import safe_path
    from creator_transactions import atomic_write_json
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:  # Imported as scripts.creator_evidence_audit in tests.
    from scripts.creator_ids import deterministic_id
    from scripts.creator_state_store import safe_path
    from scripts.creator_transactions import atomic_write_json
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
CONFIG_RELATIVE = Path("config/audit-judgment.json")
SCHEMAS = {
    "finding": Path("schemas/audit/finding.schema.json"),
    "remediation": Path("schemas/audit/remediation.schema.json"),
    "addendum": Path("schemas/audit/correction-addendum.schema.json"),
    "handoff": Path("schemas/audit/execution-handoff.schema.json"),
}
AUDIT_ID_RE = re.compile(r"^AUDIT-[A-Z0-9-]+$")


class EvidenceAuditError(RuntimeError):
    """Raised when an audit artifact cannot be created without violating policy."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceAuditError(f"{label} must be non-empty")
    return value.strip()


def _parse_time(value: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise EvidenceAuditError("timestamp must be ISO-8601") from exc


def load_judgment_config(root: Path = ROOT) -> dict[str, Any]:
    path = Path(root) / CONFIG_RELATIVE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceAuditError(f"cannot load audit judgment config: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "1.0.0":
        raise EvidenceAuditError("audit judgment config schema_version must be 1.0.0")
    severity = value.get("severity")
    bands = value.get("confidence_bands")
    qualities = value.get("evidence_quality")
    disagreements = value.get("disagreement_states")
    formula = value.get("risk_formula")
    if not isinstance(severity, dict) or set(severity) != {"informational", "low", "medium", "high", "critical"}:
        raise EvidenceAuditError("audit severity definitions are incomplete")
    if not isinstance(bands, list) or not bands or not all(isinstance(item, dict) for item in bands):
        raise EvidenceAuditError("confidence_bands must be a non-empty array")
    minimums = [item.get("minimum") for item in bands]
    if not all(isinstance(item, (int, float)) for item in minimums) or minimums != sorted(minimums, reverse=True):
        raise EvidenceAuditError("confidence_bands must be ordered by descending minimum")
    if not isinstance(qualities, dict) or set(qualities) != {"weak", "moderate", "strong", "direct"}:
        raise EvidenceAuditError("evidence quality definitions are incomplete")
    if disagreements != ["none", "noted", "material", "unresolved"]:
        raise EvidenceAuditError("disagreement states are invalid")
    if not isinstance(formula, dict) or set(formula.get("weights", {})) != {"blast_radius", "coupling_risk", "regression_risk"}:
        raise EvidenceAuditError("risk formula is invalid")
    return value


def _schema_validate(value: dict[str, Any], kind: str, schema_root: Path) -> None:
    findings = validate_json_schema(value, load_schema(schema_root / SCHEMAS[kind]))
    if findings:
        raise EvidenceAuditError(f"{kind} failed schema validation: " + "; ".join(findings))


def _audit_dir(root: Path, audit_id: str) -> Path:
    if not AUDIT_ID_RE.fullmatch(audit_id):
        raise EvidenceAuditError("audit_id must match AUDIT-[A-Z0-9-]+")
    return safe_path(root, Path(".creator/audits") / audit_id)


def _artifact_path(root: Path, audit_id: str, category: str, artifact_id: str) -> Path:
    return _audit_dir(root, audit_id) / category / f"{artifact_id}.json"


def _write_once(path: Path, value: dict[str, Any], kind: str, schema_root: Path) -> None:
    if path.exists():
        raise EvidenceAuditError(f"audit artifact already exists: {path.name}")
    _schema_validate(value, kind, schema_root)
    atomic_write_json(path, value, validator=lambda candidate: _schema_validate(json.loads(candidate.read_text(encoding="utf-8")), kind, schema_root), mode=0o600)


def _citation(root: Path, relative: str) -> str:
    path = safe_path(root, relative)
    if not path.is_file() or path.is_symlink():
        raise EvidenceAuditError(f"evidence source must be a regular repository file: {relative}")
    data = path.read_bytes()
    try:
        line_count = max(1, len(data.decode("utf-8").splitlines()))
    except UnicodeDecodeError:
        line_count = 1
    digest = hashlib.sha256(data).hexdigest()
    return f"{Path(relative).as_posix()}#L1-L{line_count}@sha256:{digest}"


def _citations(root: Path, evidence_paths: list[str]) -> list[str]:
    if not evidence_paths:
        raise EvidenceAuditError("at least one evidence source is required")
    return sorted({_citation(root, item) for item in evidence_paths})


def confidence_band(confidence: float, config: dict[str, Any]) -> str:
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        raise EvidenceAuditError("confidence must be between 0 and 1")
    for item in config["confidence_bands"]:
        if float(confidence) >= float(item["minimum"]):
            return str(item["band"])
    raise EvidenceAuditError("confidence band configuration has no fallback")


def calculate_risk(blast_radius: str, coupling_risk: str, regression_risk: str, config: dict[str, Any]) -> tuple[int, str, str]:
    formula = config["risk_formula"]
    values = formula["values"]
    weights = formula["weights"]
    dimensions = {"blast_radius": blast_radius, "coupling_risk": coupling_risk, "regression_risk": regression_risk}
    if any(level not in values for level in dimensions.values()):
        raise EvidenceAuditError("risk dimensions must be low, medium, or high")
    score = sum(int(values[level]) * int(weights[name]) for name, level in dimensions.items())
    level = next((item["level"] for item in formula["thresholds"] if score <= int(item["maximum"])), None)
    if level is None:
        raise EvidenceAuditError("risk score exceeds configured thresholds")
    return score, str(level), str(formula["expression"])


def issue_finding(
    root: Path,
    audit_id: str,
    *,
    title: str,
    observation: str,
    interpretation: str,
    judgment: str,
    severity: str,
    confidence: float,
    evidence_quality: str,
    evidence_paths: list[str],
    disagreements: list[str] | None,
    disagreement_state: str,
    limitations: list[str] | None,
    actor: str,
    issued_at: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve(); schema_root = Path(schema_root).resolve(); issued_at = issued_at or _now(); _parse_time(issued_at)
    config = load_judgment_config(schema_root)
    title = _require_text(title, "title"); observation = _require_text(observation, "observation"); interpretation = _require_text(interpretation, "interpretation"); judgment = _require_text(judgment, "judgment"); actor = _require_text(actor, "actor")
    if severity not in config["severity"]:
        raise EvidenceAuditError(f"unsupported severity: {severity}")
    if evidence_quality not in config["evidence_quality"]:
        raise EvidenceAuditError(f"unsupported evidence quality: {evidence_quality}")
    if severity == "critical" and (evidence_quality not in {"strong", "direct"} or float(confidence) < 0.75):
        raise EvidenceAuditError("critical severity requires strong or direct evidence and confidence of at least 0.75")
    disagreements = [item.strip() for item in (disagreements or []) if isinstance(item, str) and item.strip()]
    limitations = [item.strip() for item in (limitations or []) if isinstance(item, str) and item.strip()]
    if disagreement_state not in config["disagreement_states"]:
        raise EvidenceAuditError(f"unsupported disagreement state: {disagreement_state}")
    if disagreement_state == "none" and disagreements:
        raise EvidenceAuditError("disagreement_state none cannot contain disagreements")
    if disagreement_state in {"material", "unresolved"} and not disagreements:
        raise EvidenceAuditError(f"{disagreement_state} disagreement state requires evidence")
    citations = _citations(root, evidence_paths)
    finding_id = deterministic_id("FIND", audit_id, title, observation, issued_at)
    finding = {
        "schema_version": "1.0.0", "audit_id": audit_id, "finding_id": finding_id, "title": title,
        "observation": observation, "interpretation": interpretation, "judgment": judgment,
        "severity": severity, "severity_definition": config["severity"][severity]["definition"],
        "confidence": float(confidence), "confidence_band": confidence_band(float(confidence), config),
        "evidence_quality": evidence_quality, "evidence_sources": citations,
        "disagreement_state": disagreement_state, "disagreements": disagreements, "limitations": limitations,
        "status": "active", "issued_by": actor, "issued_at": issued_at,
    }
    _write_once(_artifact_path(root, audit_id, "findings", finding_id), finding, "finding", schema_root)
    return finding


def _load_artifact(root: Path, audit_id: str, category: str, artifact_id: str) -> dict[str, Any]:
    path = _artifact_path(root, audit_id, category, artifact_id)
    if not path.is_file():
        raise EvidenceAuditError(f"unknown audit artifact: {artifact_id}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceAuditError(f"invalid audit artifact {artifact_id}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceAuditError(f"audit artifact root must be an object: {artifact_id}")
    return value


def plan_remediation(
    root: Path,
    audit_id: str,
    finding_id: str,
    *,
    remediation_type: str,
    intervention_level: str,
    blast_radius: str,
    coupling_risk: str,
    regression_risk: str,
    confidence: float,
    verification_gate: str,
    rollback_criteria: str,
    recommended_action: str,
    actor: str,
    created_at: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve(); schema_root = Path(schema_root).resolve(); created_at = created_at or _now(); _parse_time(created_at)
    config = load_judgment_config(schema_root); finding = _load_artifact(root, audit_id, "findings", finding_id)
    if intervention_level == "executing":
        raise EvidenceAuditError("Evidence Audit may plan or authorize remediation but must not execute target changes")
    score, risk_level, expression = calculate_risk(blast_radius, coupling_risk, regression_risk, config)
    actor = _require_text(actor, "actor"); verification_gate = _require_text(verification_gate, "verification_gate"); rollback_criteria = _require_text(rollback_criteria, "rollback_criteria"); recommended_action = _require_text(recommended_action, "recommended_action")
    task_id = deterministic_id("REM", audit_id, finding_id, remediation_type, created_at)
    task = {
        "schema_version": "1.0.0", "audit_id": audit_id, "task_id": task_id, "source_finding": finding_id,
        "remediation_type": remediation_type, "intervention_level": intervention_level,
        "blast_radius": blast_radius, "coupling_risk": coupling_risk, "regression_risk": regression_risk,
        "risk_score": score, "risk_level": risk_level, "risk_formula": expression,
        "confidence": float(confidence), "confidence_band": confidence_band(float(confidence), config),
        "evidence_sources": finding["evidence_sources"], "verification_gate": verification_gate,
        "rollback_criteria": rollback_criteria, "handoff": "creator-execution-cycle",
        "recommended_action": recommended_action, "created_by": actor, "created_at": created_at,
    }
    _write_once(_artifact_path(root, audit_id, "remediation", task_id), task, "remediation", schema_root)
    return task


def add_correction(
    root: Path,
    audit_id: str,
    finding_id: str,
    *,
    correction_type: str,
    evidence_paths: list[str],
    updated_judgment: str,
    reason: str,
    actor: str,
    issued_at: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve(); schema_root = Path(schema_root).resolve(); issued_at = issued_at or _now(); _parse_time(issued_at)
    finding_path = _artifact_path(root, audit_id, "findings", finding_id); finding = _load_artifact(root, audit_id, "findings", finding_id)
    original_bytes = finding_path.read_bytes(); original_sha = hashlib.sha256(original_bytes).hexdigest()
    updated_judgment = _require_text(updated_judgment, "updated_judgment"); reason = _require_text(reason, "reason"); actor = _require_text(actor, "actor")
    resulting_status = "superseded" if correction_type == "supersede" else "corrected" if correction_type == "correct" else "active"
    citations = _citations(root, evidence_paths)
    addendum_id = deterministic_id("ADDENDUM", audit_id, finding_id, correction_type, citations, issued_at)
    addendum = {
        "schema_version": "1.0.0", "audit_id": audit_id, "addendum_id": addendum_id,
        "source_finding": finding_id, "correction_type": correction_type, "new_evidence": citations,
        "preserves_original": True, "original_sha256": original_sha, "previous_judgment": finding["judgment"],
        "updated_judgment": updated_judgment, "resulting_status": resulting_status,
        "reason": reason, "issued_by": actor, "issued_at": issued_at,
    }
    _write_once(_artifact_path(root, audit_id, "addenda", addendum_id), addendum, "addendum", schema_root)
    if finding_path.read_bytes() != original_bytes:
        raise EvidenceAuditError("issued finding changed while writing correction addendum")
    return addendum


def create_execution_handoff(
    root: Path,
    audit_id: str,
    *,
    finding_ids: list[str],
    task_ids: list[str],
    dependency_graph: list[dict[str, Any]],
    risks: list[str],
    verification_gates: list[str],
    rollback_criteria: list[str],
    authorization_status: str,
    actor: str | None,
    generated_at: str | None = None,
    schema_root: Path = ROOT,
) -> dict[str, Any]:
    root = Path(root).resolve(); schema_root = Path(schema_root).resolve(); generated_at = generated_at or _now(); _parse_time(generated_at)
    finding_ids = sorted(set(_require_text(item, "finding_id") for item in finding_ids)); task_ids = sorted(set(_require_text(item, "task_id") for item in task_ids))
    if not finding_ids or not task_ids:
        raise EvidenceAuditError("handoff requires at least one finding and remediation task")
    for item in finding_ids: _load_artifact(root, audit_id, "findings", item)
    for item in task_ids:
        task = _load_artifact(root, audit_id, "remediation", item)
        if task.get("source_finding") not in finding_ids:
            raise EvidenceAuditError(f"remediation {item} is not linked to a selected finding")
    risks = [_require_text(item, "risk") for item in risks]; verification_gates = [_require_text(item, "verification_gate") for item in verification_gates]; rollback_criteria = [_require_text(item, "rollback_criterion") for item in rollback_criteria]
    if not verification_gates or not rollback_criteria:
        raise EvidenceAuditError("handoff requires verification and rollback criteria")
    if authorization_status == "approved":
        actor = _require_text(actor or "", "actor")
        authorized_at: str | None = generated_at
    elif authorization_status == "planned":
        actor = None
        authorized_at = None
    else:
        raise EvidenceAuditError("authorization_status must be planned or approved")
    handoff_id = deterministic_id("AUDITHANDOFF", audit_id, finding_ids, task_ids, authorization_status, generated_at).replace("AUDITHANDOFF-", "AUDIT-HANDOFF-", 1)
    handoff = {
        "schema_version": "1.0.0", "audit_id": audit_id, "handoff_id": handoff_id,
        "target_skill": "creator-execution-cycle", "source_findings": finding_ids, "tasks": task_ids,
        "dependency_graph": dependency_graph, "risks": risks, "verification_gates": verification_gates,
        "rollback_criteria": rollback_criteria, "authorization_status": authorization_status,
        "authorized_by": actor, "authorized_at": authorized_at, "generated_at": generated_at,
    }
    _write_once(_artifact_path(root, audit_id, "handoffs", handoff_id), handoff, "handoff", schema_root)
    return handoff


def audit_status(root: Path, audit_id: str) -> dict[str, Any]:
    root = Path(root).resolve(); base = _audit_dir(root, audit_id)
    findings = {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in sorted((base / "findings").glob("*.json"))} if (base / "findings").is_dir() else {}
    addenda = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((base / "addenda").glob("*.json"))] if (base / "addenda").is_dir() else []
    effective = {finding_id: item.get("status", "active") for finding_id, item in findings.items()}
    for addendum in sorted(addenda, key=lambda item: (item.get("issued_at", ""), item.get("addendum_id", ""))):
        source = addendum.get("source_finding")
        if source in effective:
            effective[source] = addendum.get("resulting_status", effective[source])
    counts = {}
    for category in ("findings", "remediation", "addenda", "handoffs"):
        directory = base / category
        counts[category] = len(list(directory.glob("*.json"))) if directory.is_dir() else 0
    return {"schema_version": "1.0.0", "audit_id": audit_id, "counts": counts, "effective_finding_status": effective}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    issue = sub.add_parser("issue-finding"); issue.add_argument("--root", type=Path, default=Path.cwd()); issue.add_argument("--audit-id", required=True); issue.add_argument("--title", required=True); issue.add_argument("--observation", required=True); issue.add_argument("--interpretation", required=True); issue.add_argument("--judgment", required=True); issue.add_argument("--severity", required=True); issue.add_argument("--confidence", type=float, required=True); issue.add_argument("--evidence-quality", required=True); issue.add_argument("--evidence", action="append", required=True); issue.add_argument("--disagreement", action="append", default=[]); issue.add_argument("--disagreement-state", default="none"); issue.add_argument("--limitation", action="append", default=[]); issue.add_argument("--actor", required=True); issue.add_argument("--issued-at")
    remediate = sub.add_parser("plan-remediation"); remediate.add_argument("--root", type=Path, default=Path.cwd()); remediate.add_argument("--audit-id", required=True); remediate.add_argument("--finding-id", required=True); remediate.add_argument("--remediation-type", required=True); remediate.add_argument("--intervention-level", required=True); remediate.add_argument("--blast-radius", required=True); remediate.add_argument("--coupling-risk", required=True); remediate.add_argument("--regression-risk", required=True); remediate.add_argument("--confidence", type=float, required=True); remediate.add_argument("--verification-gate", required=True); remediate.add_argument("--rollback-criteria", required=True); remediate.add_argument("--recommended-action", required=True); remediate.add_argument("--actor", required=True); remediate.add_argument("--created-at")
    correction = sub.add_parser("add-correction"); correction.add_argument("--root", type=Path, default=Path.cwd()); correction.add_argument("--audit-id", required=True); correction.add_argument("--finding-id", required=True); correction.add_argument("--correction-type", choices=("clarify", "correct", "supersede"), required=True); correction.add_argument("--evidence", action="append", required=True); correction.add_argument("--updated-judgment", required=True); correction.add_argument("--reason", required=True); correction.add_argument("--actor", required=True); correction.add_argument("--issued-at")
    handoff = sub.add_parser("create-handoff"); handoff.add_argument("--root", type=Path, default=Path.cwd()); handoff.add_argument("--audit-id", required=True); handoff.add_argument("--finding-id", action="append", required=True); handoff.add_argument("--task-id", action="append", required=True); handoff.add_argument("--dependency-graph", type=Path); handoff.add_argument("--risk", action="append", default=[]); handoff.add_argument("--verification-gate", action="append", required=True); handoff.add_argument("--rollback-criteria", action="append", required=True); handoff.add_argument("--authorization-status", choices=("planned", "approved"), default="planned"); handoff.add_argument("--actor"); handoff.add_argument("--generated-at")
    status = sub.add_parser("status"); status.add_argument("--root", type=Path, default=Path.cwd()); status.add_argument("--audit-id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "issue-finding": result = issue_finding(args.root, args.audit_id, title=args.title, observation=args.observation, interpretation=args.interpretation, judgment=args.judgment, severity=args.severity, confidence=args.confidence, evidence_quality=args.evidence_quality, evidence_paths=args.evidence, disagreements=args.disagreement, disagreement_state=args.disagreement_state, limitations=args.limitation, actor=args.actor, issued_at=args.issued_at)
        elif args.command == "plan-remediation": result = plan_remediation(args.root, args.audit_id, args.finding_id, remediation_type=args.remediation_type, intervention_level=args.intervention_level, blast_radius=args.blast_radius, coupling_risk=args.coupling_risk, regression_risk=args.regression_risk, confidence=args.confidence, verification_gate=args.verification_gate, rollback_criteria=args.rollback_criteria, recommended_action=args.recommended_action, actor=args.actor, created_at=args.created_at)
        elif args.command == "add-correction": result = add_correction(args.root, args.audit_id, args.finding_id, correction_type=args.correction_type, evidence_paths=args.evidence, updated_judgment=args.updated_judgment, reason=args.reason, actor=args.actor, issued_at=args.issued_at)
        elif args.command == "create-handoff":
            graph = json.loads(args.dependency_graph.read_text(encoding="utf-8")) if args.dependency_graph else []
            if not isinstance(graph, list): raise EvidenceAuditError("dependency graph must be a JSON array")
            result = create_execution_handoff(args.root, args.audit_id, finding_ids=args.finding_id, task_ids=args.task_id, dependency_graph=graph, risks=args.risk, verification_gates=args.verification_gate, rollback_criteria=args.rollback_criteria, authorization_status=args.authorization_status, actor=args.actor, generated_at=args.generated_at)
        else: result = audit_status(args.root, args.audit_id)
    except (EvidenceAuditError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Creator Evidence Audit failed: {exc}", file=sys.stderr); return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
