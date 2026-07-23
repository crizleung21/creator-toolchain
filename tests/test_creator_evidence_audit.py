from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.creator_evidence_audit import (
    EvidenceAuditError,
    add_correction,
    audit_status,
    create_execution_handoff,
    issue_finding,
    plan_remediation,
)

ROOT = Path(__file__).resolve().parents[1]
AUDIT_ID = "AUDIT-DEMO"
TS1 = "2026-07-18T10:30:00Z"
TS2 = "2026-07-18T10:31:00Z"
TS3 = "2026-07-18T10:32:00Z"
TS4 = "2026-07-18T10:33:00Z"


class CreatorEvidenceAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        (self.root / "evidence").mkdir()
        self.source = self.root / "evidence/source.txt"
        self.source.write_text("line one\nline two\n", encoding="utf-8")

    def finding(self):
        return issue_finding(
            self.root,
            AUDIT_ID,
            title="Missing release gate",
            observation="The release evidence file is absent.",
            interpretation="Release readiness is not established.",
            judgment="The package must not be released as stable.",
            severity="high",
            confidence=0.95,
            evidence_quality="direct",
            evidence_paths=["evidence/source.txt"],
            disagreements=[],
            disagreement_state="none",
            limitations=["Only the supplied repository evidence was reviewed."],
            actor="auditor",
            issued_at=TS1,
            schema_root=ROOT,
        )

    def test_finding_uses_portable_citation_and_does_not_mutate_target(self) -> None:
        before = self.source.read_bytes()
        finding = self.finding()
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(finding["confidence_band"], "very_high")
        self.assertIn("evidence/source.txt#L1-L2@sha256:", finding["evidence_sources"][0])
        self.assertTrue((self.root / f".creator/audits/{AUDIT_ID}/findings/{finding['finding_id']}.json").is_file())

    def test_duplicate_finding_is_zero_write(self) -> None:
        finding = self.finding()
        path = self.root / f".creator/audits/{AUDIT_ID}/findings/{finding['finding_id']}.json"
        before = path.read_bytes()
        with self.assertRaises(EvidenceAuditError):
            self.finding()
        self.assertEqual(path.read_bytes(), before)

    def test_remediation_risk_is_deterministic_and_execution_is_rejected(self) -> None:
        finding = self.finding()
        task = plan_remediation(
            self.root, AUDIT_ID, finding["finding_id"], remediation_type="workflow", intervention_level="planning",
            blast_radius="medium", coupling_risk="low", regression_risk="high", confidence=0.8,
            verification_gate="Run the full release gate suite.", rollback_criteria="Restore the prior workflow bytes.",
            recommended_action="Hand off the approved repair plan.", actor="auditor", created_at=TS2, schema_root=ROOT,
        )
        self.assertEqual(task["risk_score"], 20)
        self.assertEqual(task["risk_level"], "medium")
        with self.assertRaises(EvidenceAuditError):
            plan_remediation(
                self.root, AUDIT_ID, finding["finding_id"], remediation_type="code", intervention_level="executing",
                blast_radius="low", coupling_risk="low", regression_risk="low", confidence=0.8,
                verification_gate="tests", rollback_criteria="restore", recommended_action="execute",
                actor="auditor", created_at=TS3, schema_root=ROOT,
            )

    def test_correction_addendum_preserves_original_bytes_and_derives_status(self) -> None:
        finding = self.finding()
        finding_path = self.root / f".creator/audits/{AUDIT_ID}/findings/{finding['finding_id']}.json"
        before = finding_path.read_bytes()
        self.source.write_text("line one\nline two\nline three\n", encoding="utf-8")
        addendum = add_correction(
            self.root, AUDIT_ID, finding["finding_id"], correction_type="correct",
            evidence_paths=["evidence/source.txt"], updated_judgment="The gap is narrower than first reported.",
            reason="New direct evidence was added.", actor="auditor", issued_at=TS2, schema_root=ROOT,
        )
        self.assertTrue(addendum["preserves_original"])
        self.assertEqual(finding_path.read_bytes(), before)
        self.assertEqual(audit_status(self.root, AUDIT_ID)["effective_finding_status"][finding["finding_id"]], "corrected")

    def test_handoff_links_existing_finding_and_task(self) -> None:
        finding = self.finding()
        task = plan_remediation(
            self.root, AUDIT_ID, finding["finding_id"], remediation_type="workflow", intervention_level="authorizing",
            blast_radius="low", coupling_risk="low", regression_risk="medium", confidence=0.9,
            verification_gate="Run tests.", rollback_criteria="Restore prior bytes.", recommended_action="Execute after approval.",
            actor="auditor", created_at=TS2, schema_root=ROOT,
        )
        handoff = create_execution_handoff(
            self.root, AUDIT_ID, finding_ids=[finding["finding_id"]], task_ids=[task["task_id"]],
            dependency_graph=[], risks=["Regression risk"], verification_gates=["All tests pass"],
            rollback_criteria=["Restore prior bytes"], authorization_status="approved", actor="owner",
            generated_at=TS3, schema_root=ROOT,
        )
        self.assertEqual(handoff["target_skill"], "creator-execution-cycle")
        self.assertEqual(handoff["authorized_by"], "owner")
        with self.assertRaises(EvidenceAuditError):
            create_execution_handoff(
                self.root, AUDIT_ID, finding_ids=[finding["finding_id"]], task_ids=["REM-AAAAAAAA"],
                dependency_graph=[], risks=[], verification_gates=["tests"], rollback_criteria=["restore"],
                authorization_status="planned", actor=None, generated_at=TS4, schema_root=ROOT,
            )

    def test_unsafe_or_missing_evidence_is_rejected_without_audit_tree(self) -> None:
        with self.assertRaises(RuntimeError):
            issue_finding(
                self.root, AUDIT_ID, title="Unsafe evidence", observation="Missing.", interpretation="Unknown.", judgment="Cannot judge.",
                severity="low", confidence=0.5, evidence_quality="weak", evidence_paths=["../outside.txt"],
                disagreements=[], disagreement_state="none", limitations=[], actor="auditor", issued_at=TS1, schema_root=ROOT,
            )
        self.assertFalse((self.root / ".creator/audits").exists())

    def test_material_disagreement_requires_detail(self) -> None:
        with self.assertRaises(EvidenceAuditError):
            issue_finding(
                self.root, AUDIT_ID, title="Disputed", observation="Observed.", interpretation="Interpreted.", judgment="Judged.",
                severity="medium", confidence=0.6, evidence_quality="moderate", evidence_paths=["evidence/source.txt"],
                disagreements=[], disagreement_state="material", limitations=[], actor="auditor", issued_at=TS1, schema_root=ROOT,
            )

    def test_critical_severity_requires_strong_evidence(self) -> None:
        with self.assertRaises(EvidenceAuditError):
            issue_finding(
                self.root, AUDIT_ID, title="Critical claim", observation="Observed.", interpretation="Interpreted.", judgment="Critical.",
                severity="critical", confidence=0.6, evidence_quality="weak", evidence_paths=["evidence/source.txt"],
                disagreements=[], disagreement_state="none", limitations=[], actor="auditor", issued_at=TS1, schema_root=ROOT,
            )


if __name__ == "__main__":
    unittest.main()
