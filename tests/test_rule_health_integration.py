from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.creator_health_check import calculate_health
from scripts.creator_rule_cli import _build_parser, main as rule_cli_main
from scripts.creator_rule_conflicts import (
    CONFLICT_REPORT_RELATIVE,
    audit_rules,
    write_conflict_report,
)
from scripts.creator_rule_store import approve_proposal, stage_proposal

ROOT = Path(__file__).resolve().parents[1]
AUDITED_AT = "2026-07-18T08:30:00Z"
REVIEW_DATE = "2027-07-18T00:00:00Z"


class RuleHealthIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        shutil.copytree(ROOT / ".creator", self.root / ".creator")
        architecture = self.root / "docs/architecture"
        architecture.mkdir(parents=True)
        shutil.copy2(
            ROOT / "docs/architecture/creator-toolchain.md",
            architecture / "creator-toolchain.md",
        )

    def _rules(self) -> tuple[Path, dict]:
        path = self.root / ".creator/rules.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def _write_rules(self, value: dict) -> None:
        (self.root / ".creator/rules.json").write_text(
            json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_blocking_rule_conflict_is_red_health(self) -> None:
        _, rules = self._rules()
        global_rule = dict(rules["domains"][0]["rules"][0])
        global_rule["rule_id"] = "CODE-999"
        coding = next(item for item in rules["domains"] if item["domain_id"] == "coding")
        coding["rules"].append(global_rule)
        self._write_rules(rules)

        report = calculate_health(
            self.root,
            calculated_at=AUDITED_AT,
            include_repository_checks=False,
            schema_root=ROOT,
        )

        self.assertEqual(report["level"], "red")
        self.assertTrue(
            any(item["signal_id"] == "RULE_CONFLICT_BLOCKING" for item in report["signals"])
        )

    def test_advisory_rule_conflict_is_amber_health(self) -> None:
        _, rules = self._rules()
        coding = next(item for item in rules["domains"] if item["domain_id"] == "coding")
        safety = next(item for item in rules["domains"] if item["domain_id"] == "safety")
        coding["trigger_keywords"].append("shared-governance-trigger")
        safety["trigger_keywords"].append("shared-governance-trigger")
        self._write_rules(rules)

        report = calculate_health(
            self.root,
            calculated_at=AUDITED_AT,
            include_repository_checks=False,
            schema_root=ROOT,
        )

        self.assertEqual(report["level"], "amber")
        self.assertTrue(
            any(item["signal_id"] == "RULE_CONFLICT_ADVISORY" for item in report["signals"])
        )

    def test_conflict_report_write_is_derived_and_rule_bytes_are_unchanged(self) -> None:
        rules_path, _ = self._rules()
        before = rules_path.read_bytes()
        report = audit_rules(self.root, audited_at=AUDITED_AT, schema_root=ROOT)
        relative = write_conflict_report(self.root, report, schema_root=ROOT)

        self.assertEqual(relative, CONFLICT_REPORT_RELATIVE.as_posix())
        self.assertEqual(before, rules_path.read_bytes())
        stored = json.loads((self.root / CONFLICT_REPORT_RELATIVE).read_text(encoding="utf-8"))
        self.assertEqual(stored, report)

    def test_advisory_conflicts_are_linked_from_approval_decision(self) -> None:
        _, rules = self._rules()
        coding = next(item for item in rules["domains"] if item["domain_id"] == "coding")
        safety = next(item for item in rules["domains"] if item["domain_id"] == "safety")
        coding["trigger_keywords"].append("shared-governance-trigger")
        safety["trigger_keywords"].append("shared-governance-trigger")
        self._write_rules(rules)

        rule = {
            "rule_id": "CODE-998",
            "severity": "medium",
            "text": "Preserve deterministic test evidence.",
            "status": "active",
            "scope": "test evidence",
            "source": "unit-test",
            "created_at": AUDITED_AT,
            "updated_at": AUDITED_AT,
            "review_date": REVIEW_DATE,
        }
        staged = stage_proposal(
            self.root,
            operation="add-rule",
            affected_domains=["coding"],
            payload={"domain_id": "coding", "rule": rule},
            requested_by="tester",
            source="unit-test",
            rationale="candidate",
            expected_behavior_change="add evidence rule",
            review_date=REVIEW_DATE,
            timestamp=AUDITED_AT,
            schema_root=ROOT,
        )
        result = approve_proposal(
            self.root,
            staged["proposal"]["proposal_id"],
            actor="reviewer",
            rationale="approved with advisory evidence",
            timestamp="2026-07-18T08:31:00Z",
            schema_root=ROOT,
        )
        advisory_ids = {
            item["conflict_id"]
            for item in result["conflict_report"]["conflicts"]
            if not item["blocking"]
        }
        self.assertTrue(advisory_ids)
        self.assertTrue(advisory_ids.issubset(set(result["decision"]["conflict_refs"])))


class CreatorRuleCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        (self.root / ".creator").mkdir()
        shutil.copy2(ROOT / ".creator/rules.json", self.root / ".creator/rules.json")
        shutil.copy2(ROOT / ".creator/decisions.json", self.root / ".creator/decisions.json")

    def test_cli_exposes_every_declared_operation(self) -> None:
        parser = _build_parser()
        choices = next(
            action.choices
            for action in parser._actions
            if isinstance(action, __import__("argparse")._SubParsersAction)
        )
        self.assertEqual(
            set(choices),
            {
                "list-domains",
                "get-domain",
                "preflight",
                "create-domain",
                "toggle-domain",
                "add-rule",
                "remove-rule",
                "replace-rule",
                "stage-proposal",
                "approve-proposal",
                "reject-proposal",
                "recall",
                "exclude",
                "list-commands",
                "add-command",
                "search-decisions",
                "audit-conflicts",
            },
        )

    def test_cli_audit_write_persists_report_without_rule_mutation(self) -> None:
        rules_path = self.root / ".creator/rules.json"
        before = rules_path.read_bytes()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = rule_cli_main(
                [
                    "audit-conflicts",
                    "--root",
                    str(self.root),
                    "--audited-at",
                    AUDITED_AT,
                    "--write",
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(before, rules_path.read_bytes())
        self.assertTrue((self.root / CONFLICT_REPORT_RELATIVE).is_file())
        self.assertEqual(json.loads(stdout.getvalue())["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
