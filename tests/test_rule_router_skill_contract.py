from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE = ROOT / ".agents/skills/creator-rule-router"
PLUGIN = ROOT / "plugin/creator-toolchain/skills/creator-rule-router"


class RuleRouterSkillContractTests(unittest.TestCase):
    def test_skill_declares_complete_governance_contract(self) -> None:
        text = (AUTHORITATIVE / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "## Mode-to-Resource Map",
            "creator-rules:preflight",
            "creator-rules:stage-proposal",
            "creator-rules:approve-proposal",
            "creator-rules:reject-proposal",
            "creator-rules:recall",
            "creator-rules:exclude",
            "creator-rules:audit-conflicts",
            "RULE_CONFLICT_BLOCKING",
            "RULE_CONFLICT_ADVISORY",
            "Do not auto-promote",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_required_rule_resources_exist(self) -> None:
        required = {
            "SKILL.md",
            "references/rule-preflight.md",
            "references/context-budget.md",
            "references/rule-schema.md",
            "references/rule-operations.md",
            "references/proposal-approval.md",
            "references/conflict-resolution.md",
            "assets/rule-preflight-template.md",
            "assets/rule-proposal-template.json",
            "assets/rule-decision-template.json",
            "assets/conflict-report-template.json",
        }
        found = {
            path.relative_to(AUTHORITATIVE).as_posix()
            for path in AUTHORITATIVE.rglob("*")
            if path.is_file()
        }
        self.assertEqual(found, required)

    def test_rule_assets_are_valid_json_where_applicable(self) -> None:
        for name in (
            "rule-proposal-template.json",
            "rule-decision-template.json",
            "conflict-report-template.json",
        ):
            with self.subTest(name=name):
                value = json.loads((AUTHORITATIVE / "assets" / name).read_text(encoding="utf-8"))
                self.assertEqual(value["schema_version"], "1.0.0")

    def test_plugin_rule_router_is_byte_equivalent(self) -> None:
        author_files = sorted(path for path in AUTHORITATIVE.rglob("*") if path.is_file())
        plugin_files = sorted(path for path in PLUGIN.rglob("*") if path.is_file())
        self.assertEqual(
            [path.relative_to(AUTHORITATIVE).as_posix() for path in author_files],
            [path.relative_to(PLUGIN).as_posix() for path in plugin_files],
        )
        for author, plugin in zip(author_files, plugin_files):
            with self.subTest(path=author.relative_to(AUTHORITATIVE).as_posix()):
                self.assertEqual(author.read_bytes(), plugin.read_bytes())


if __name__ == "__main__":
    unittest.main()
