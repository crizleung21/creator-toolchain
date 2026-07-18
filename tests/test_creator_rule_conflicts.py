from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.creator_rule_conflicts import audit_document, audit_rules
from scripts.creator_rule_store import RuleStoreError, approve_proposal, stage_proposal

ROOT = Path(__file__).resolve().parents[1]
AUDITED_AT = "2026-07-18T08:30:00Z"
REVIEW_DATE = "2027-07-18T00:00:00Z"


class CreatorRuleConflictTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(); self.addCleanup(self.tempdir.cleanup); self.root = Path(self.tempdir.name); (self.root / ".creator").mkdir()
        shutil.copy2(ROOT / ".creator/rules.json", self.root / ".creator/rules.json"); shutil.copy2(ROOT / ".creator/decisions.json", self.root / ".creator/decisions.json")

    def document(self): return json.loads((self.root / ".creator/rules.json").read_text())
    def rule(self, rid, text, review_date=REVIEW_DATE): return {"rule_id": rid, "severity": "high", "text": text, "status": "active", "scope": "state editing", "source": "unit-test", "created_at": AUDITED_AT, "updated_at": AUDITED_AT, "review_date": review_date}

    def test_current_rules_have_no_blocking_conflicts(self):
        self.assertEqual(audit_rules(self.root, audited_at=AUDITED_AT, schema_root=ROOT)["blocking_count"], 0)

    def test_duplicate_rule_text_is_blocking(self):
        document = self.document(); document["domains"][1]["rules"].append(self.rule("SAFE-003", document["domains"][0]["rules"][0]["text"]))
        self.assertTrue(any(item["conflict_type"] == "duplicate" and item["blocking"] for item in audit_document(document, audited_at=AUDITED_AT, schema_root=ROOT)["conflicts"]))

    def test_contradiction_is_blocking(self):
        document = self.document(); coding = next(item for item in document["domains"] if item["domain_id"] == "coding"); coding["rules"].extend([self.rule("CODE-010", "State may be edited."), self.rule("CODE-011", "State may not be edited.")])
        self.assertTrue(any(item["conflict_type"] == "contradiction" and item["blocking"] for item in audit_document(document, audited_at=AUDITED_AT, schema_root=ROOT)["conflicts"]))

    def test_unsafe_rule_is_blocking_but_prohibition_is_not(self):
        document = self.document(); safety = next(item for item in document["domains"] if item["domain_id"] == "safety"); safety["rules"].append(self.rule("SAFE-010", "Bypass approval for urgent state changes."))
        self.assertTrue(any(item["conflict_type"] == "unsafe_rule" for item in audit_document(document, audited_at=AUDITED_AT, schema_root=ROOT)["conflicts"])); self.assertFalse(any(item["conflict_type"] == "unsafe_rule" for item in audit_rules(self.root, audited_at=AUDITED_AT, schema_root=ROOT)["conflicts"]))

    def test_stale_rule_is_advisory(self):
        document = self.document(); coding = next(item for item in document["domains"] if item["domain_id"] == "coding"); coding["rules"].append(self.rule("CODE-012", "Record deterministic test output.", "2026-01-01T00:00:00Z"))
        stale = [item for item in audit_document(document, audited_at=AUDITED_AT, schema_root=ROOT)["conflicts"] if item["conflict_type"] == "stale_rule"]; self.assertTrue(stale); self.assertTrue(all(not item["blocking"] for item in stale))

    def test_duplicate_command_is_blocking(self):
        document = self.document(); coding = next(item for item in document["domains"] if item["domain_id"] == "coding"); coding["commands"].append({"command_id": "validate-coding", "trigger": "validate creator toolchain", "workflow": "python3 scripts/validate_creator_toolchain.py --scope all", "status": "active", "source": "unit-test", "created_at": AUDITED_AT, "updated_at": AUDITED_AT})
        self.assertTrue(any(item["conflict_type"] == "duplicate_command" and item["blocking"] for item in audit_document(document, audited_at=AUDITED_AT, schema_root=ROOT)["conflicts"]))

    def test_approval_blocks_unsafe_candidate_without_apply_write(self):
        staged = stage_proposal(self.root, operation="add-rule", affected_domains=["safety"], payload={"domain_id": "safety", "rule": self.rule("SAFE-020", "Bypass approval for urgent state changes.")}, requested_by="tester", source="unit-test", rationale="negative test", expected_behavior_change="must not activate", review_date=REVIEW_DATE, timestamp=AUDITED_AT, schema_root=ROOT)
        path = self.root / ".creator/rules.json"; before = path.read_bytes()
        with self.assertRaises(RuleStoreError): approve_proposal(self.root, staged["proposal"]["proposal_id"], actor="reviewer", rationale="attempt", timestamp="2026-07-18T08:31:00Z", schema_root=ROOT)
        self.assertEqual(before, path.read_bytes())


if __name__ == "__main__": unittest.main()
