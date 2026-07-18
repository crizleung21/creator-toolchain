from __future__ import annotations

import unittest
from pathlib import Path

from scripts.json_schema_lite import load_schema, validate

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas/audit"
EXPECTED = {"finding", "remediation", "correction-addendum", "execution-handoff"}


class AuditSchemaAssetTests(unittest.TestCase):
    def test_expected_audit_schemas_exist(self) -> None:
        self.assertEqual({path.stem.removesuffix(".schema") for path in SCHEMA_ROOT.glob("*.schema.json")}, EXPECTED)

    def test_valid_examples_pass(self) -> None:
        examples = {
            "finding": {
                "schema_version": "1.0.0", "finding_id": "FIND-001", "title": "Missing gate", "observation": "The artifact is absent.", "interpretation": "Closure is incomplete.", "judgment": "Execution cannot be considered complete.", "severity": "high", "confidence": 0.9, "evidence_quality": "direct", "evidence_sources": ["path/file"], "disagreements": [], "limitations": [], "status": "active", "issued_at": "2026-07-18T10:15:00Z"
            },
            "remediation": {
                "schema_version": "1.0.0", "task_id": "REM-001", "source_finding": "FIND-001", "remediation_type": "workflow", "intervention_level": "planning", "blast_radius": "medium", "coupling_risk": "low", "regression_risk": "medium", "risk_score": 5, "confidence": 0.85, "evidence_sources": ["path/file"], "verification_gate": "Run tests.", "rollback_criteria": "Restore prior bytes.", "handoff": "creator-execution-cycle"
            },
            "correction-addendum": {
                "schema_version": "1.0.0", "addendum_id": "ADDENDUM-001", "source_finding": "FIND-001", "correction_type": "correct", "new_evidence": ["new/path"], "preserves_original": True, "updated_judgment": "The finding is narrowed.", "issued_at": "2026-07-18T10:20:00Z"
            },
            "execution-handoff": {
                "schema_version": "1.0.0", "handoff_id": "AUDIT-HANDOFF-001", "target_skill": "creator-execution-cycle", "source_findings": ["FIND-001"], "tasks": ["REM-001"], "dependency_graph": [], "risks": ["regression"], "verification_gates": ["tests pass"], "rollback_criteria": ["restore prior bytes"], "authorization_status": "planned"
            },
        }
        for name, example in examples.items():
            with self.subTest(schema=name):
                self.assertEqual(validate(example, load_schema(SCHEMA_ROOT / f"{name}.schema.json")), [])

    def test_malformed_finding_is_rejected(self) -> None:
        schema = load_schema(SCHEMA_ROOT / "finding.schema.json")
        findings = validate({"schema_version": "1.0.0", "finding_id": "bad"}, schema)
        self.assertTrue(findings)
        self.assertTrue(any("observation" in item or "finding_id" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
