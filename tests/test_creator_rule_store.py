from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.creator_rule_store import RuleStoreError, add_command, add_rule, approve_proposal, get_domain, list_commands, load_rules, preflight, recall, reject_proposal, stage_proposal

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = "2026-07-18T08:00:00Z"
REVIEW_DATE = "2027-07-18T00:00:00Z"


class CreatorRuleStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(); self.addCleanup(self.tempdir.cleanup); self.root = Path(self.tempdir.name); (self.root / ".creator").mkdir()
        shutil.copy2(ROOT / ".creator/rules.json", self.root / ".creator/rules.json"); shutil.copy2(ROOT / ".creator/decisions.json", self.root / ".creator/decisions.json")

    def rule(self, rule_id: str, text: str = "Use Hong Kong terminology when the active context requests it.") -> dict[str, object]:
        return {"rule_id": rule_id, "severity": "medium", "text": text, "status": "active", "scope": "Hong Kong terminology", "source": "unit-test", "created_at": TIMESTAMP, "updated_at": TIMESTAMP, "review_date": REVIEW_DATE}

    def test_declared_domains_and_zh_hant_preflight(self) -> None:
        document = load_rules(self.root, schema_root=ROOT)
        self.assertEqual({item["domain_id"] for item in document["domains"]}, {"GLOBAL", "creator-toolchain", "zh-hant", "coding", "safety", "creator-production", "project-execution"})
        result = preflight(self.root, "請用繁體中文審核 creator-toolchain plugin package", audited_at=TIMESTAMP, schema_root=ROOT)
        matched = {item["domain_id"] for item in result["matched_domains"]}; self.assertTrue({"GLOBAL", "creator-toolchain", "zh-hant"}.issubset(matched))
        selected = {item["rule_id"] for item in result["selected_rules"]}; self.assertIn("ZH-001", selected); self.assertIn("CT-001", selected)

    def test_empty_actor_is_zero_write(self) -> None:
        path = self.root / ".creator/rules.json"; before = path.read_bytes()
        with self.assertRaises(RuleStoreError): add_rule(self.root, "zh-hant", self.rule("ZH-003"), actor="", rationale="must fail", timestamp=TIMESTAMP, schema_root=ROOT)
        self.assertEqual(before, path.read_bytes())

    def test_stage_does_not_apply(self) -> None:
        result = stage_proposal(self.root, operation="add-rule", affected_domains=["zh-hant"], payload={"domain_id": "zh-hant", "rule": self.rule("ZH-003")}, requested_by="tester", source="unit-test", rationale="candidate", expected_behavior_change="add rule", review_date=REVIEW_DATE, timestamp=TIMESTAMP, schema_root=ROOT)
        self.assertEqual(result["status"], "staged"); self.assertNotIn("ZH-003", {item["rule_id"] for item in get_domain(self.root, "zh-hant", schema_root=ROOT)["rules"]})

    def test_approve_applies_once_and_appends_decision(self) -> None:
        staged = stage_proposal(self.root, operation="add-rule", affected_domains=["zh-hant"], payload={"domain_id": "zh-hant", "rule": self.rule("ZH-003")}, requested_by="tester", source="unit-test", rationale="candidate", expected_behavior_change="add rule", review_date=REVIEW_DATE, timestamp=TIMESTAMP, schema_root=ROOT)
        result = approve_proposal(self.root, staged["proposal"]["proposal_id"], actor="reviewer", rationale="approved", timestamp="2026-07-18T08:01:00Z", schema_root=ROOT)
        self.assertIn("ZH-003", {item["rule_id"] for item in get_domain(self.root, "zh-hant", schema_root=ROOT)["rules"]}); self.assertEqual(result["decision"]["proposal_id"], staged["proposal"]["proposal_id"])
        path = self.root / ".creator/rules.json"; before = path.read_bytes()
        with self.assertRaises(RuleStoreError): approve_proposal(self.root, staged["proposal"]["proposal_id"], actor="reviewer", rationale="duplicate", timestamp="2026-07-18T08:02:00Z", schema_root=ROOT)
        self.assertEqual(before, path.read_bytes())

    def test_reject_does_not_apply(self) -> None:
        staged = stage_proposal(self.root, operation="add-rule", affected_domains=["zh-hant"], payload={"domain_id": "zh-hant", "rule": self.rule("ZH-004")}, requested_by="tester", source="unit-test", rationale="candidate", expected_behavior_change="candidate", review_date=REVIEW_DATE, timestamp=TIMESTAMP, schema_root=ROOT)
        reject_proposal(self.root, staged["proposal"]["proposal_id"], actor="reviewer", rationale="redundant", timestamp="2026-07-18T08:01:00Z", schema_root=ROOT)
        self.assertNotIn("ZH-004", {item["rule_id"] for item in get_domain(self.root, "zh-hant", schema_root=ROOT)["rules"]})

    def test_duplicate_rule_is_zero_write(self) -> None:
        path = self.root / ".creator/rules.json"; before = path.read_bytes()
        with self.assertRaises(RuleStoreError): add_rule(self.root, "zh-hant", self.rule("GLOBAL-001"), actor="tester", rationale="duplicate", timestamp=TIMESTAMP, schema_root=ROOT)
        self.assertEqual(before, path.read_bytes())

    def test_recall_preserves_disabled_record(self) -> None:
        recall(self.root, "ZH-001", actor="reviewer", rationale="review", timestamp=TIMESTAMP, schema_root=ROOT)
        item = next(item for item in get_domain(self.root, "zh-hant", schema_root=ROOT)["rules"] if item["rule_id"] == "ZH-001"); self.assertEqual(item["status"], "disabled")

    def test_add_and_list_command(self) -> None:
        command = {"command_id": "validate-zh-hant-output", "trigger": "validate zh-hant output", "workflow": "python3 scripts/validate_zh_hant_output.py", "status": "active", "source": "unit-test", "created_at": TIMESTAMP, "updated_at": TIMESTAMP}
        add_command(self.root, "zh-hant", command, actor="reviewer", rationale="scoped command", timestamp=TIMESTAMP, schema_root=ROOT)
        self.assertEqual([item["command_id"] for item in list_commands(self.root, domain_id="zh-hant", schema_root=ROOT)], ["validate-zh-hant-output"])


if __name__ == "__main__": unittest.main()
