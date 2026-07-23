from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.creator_evidence_audit import load_judgment_config
from scripts.json_schema_lite import load_schema, validate

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas/audit"
EXPECTED = {"finding", "remediation", "correction-addendum", "execution-handoff"}
CITATION = "evidence/file.txt#L1-L2@sha256:" + "a" * 64


class AuditSchemaAssetTests(unittest.TestCase):
    def test_expected_audit_schemas_and_judgment_config_exist(self) -> None:
        self.assertEqual({path.stem.removesuffix(".schema") for path in SCHEMA_ROOT.glob("*.schema.json")}, EXPECTED)
        config = load_judgment_config(ROOT)
        self.assertEqual(config["risk_formula"]["expression"], "blast_radius*4 + coupling_risk*3 + regression_risk*3")
        self.assertEqual(set(config["severity"]), {"informational", "low", "medium", "high", "critical"})

    def test_valid_examples_pass(self) -> None:
        examples = {
            "finding": {
                "schema_version": "1.0.0", "audit_id": "AUDIT-DEMO", "finding_id": "FIND-AAAAAAAA", "title": "Missing gate", "observation": "The artifact is absent.", "interpretation": "Closure is incomplete.", "judgment": "Execution cannot be considered complete.", "severity": "high", "severity_definition": "Serious workflow defect.", "confidence": 0.9, "confidence_band": "very_high", "evidence_quality": "direct", "evidence_sources": [CITATION], "disagreement_state": "none", "disagreements": [], "limitations": [], "status": "active", "issued_by": "auditor", "issued_at": "2026-07-18T10:15:00Z"
            },
            "remediation": {
                "schema_version": "1.0.0", "audit_id": "AUDIT-DEMO", "task_id": "REM-BBBBBBBB", "source_finding": "FIND-AAAAAAAA", "remediation_type": "workflow", "intervention_level": "planning", "blast_radius": "medium", "coupling_risk": "low", "regression_risk": "medium", "risk_score": 17, "risk_level": "medium", "risk_formula": "blast_radius*4 + coupling_risk*3 + regression_risk*3", "confidence": 0.85, "confidence_band": "high", "evidence_sources": [CITATION], "verification_gate": "Run tests.", "rollback_criteria": "Restore prior bytes.", "handoff": "creator-execution-cycle", "recommended_action": "Implement through an approved execution plan.", "created_by": "auditor", "created_at": "2026-07-18T10:16:00Z"
            },
            "correction-addendum": {
                "schema_version": "1.0.0", "audit_id": "AUDIT-DEMO", "addendum_id": "ADDENDUM-CCCCCCCC", "source_finding": "FIND-AAAAAAAA", "correction_type": "correct", "new_evidence": [CITATION], "preserves_original": True, "original_sha256": "b" * 64, "previous_judgment": "Original judgment.", "updated_judgment": "The finding is narrowed.", "resulting_status": "corrected", "reason": "New direct evidence.", "issued_by": "auditor", "issued_at": "2026-07-18T10:20:00Z"
            },
            "execution-handoff": {
                "schema_version": "1.0.0", "audit_id": "AUDIT-DEMO", "handoff_id": "AUDIT-HANDOFF-DDDDDDDD", "target_skill": "creator-execution-cycle", "source_findings": ["FIND-AAAAAAAA"], "tasks": ["REM-BBBBBBBB"], "dependency_graph": [], "risks": ["regression"], "verification_gates": ["tests pass"], "rollback_criteria": ["restore prior bytes"], "authorization_status": "planned", "authorized_by": None, "authorized_at": None, "generated_at": "2026-07-18T10:21:00Z"
            },
        }
        for name, example in examples.items():
            with self.subTest(schema=name):
                self.assertEqual(validate(example, load_schema(SCHEMA_ROOT / f"{name}.schema.json")), [])

    def test_malformed_finding_is_rejected(self) -> None:
        findings = validate({"schema_version": "1.0.0", "finding_id": "bad"}, load_schema(SCHEMA_ROOT / "finding.schema.json"))
        self.assertTrue(findings)
        self.assertTrue(any("observation" in item or "finding_id" in item for item in findings))

    def test_schema_documents_are_valid_json(self) -> None:
        for path in SCHEMA_ROOT.glob("*.schema.json"):
            with self.subTest(path=path.name):
                self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)


if __name__ == "__main__":
    unittest.main()
