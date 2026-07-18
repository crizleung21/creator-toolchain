from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE = ROOT / ".agents/skills/creator-intake-planner"
PLUGIN = ROOT / "plugin/creator-toolchain/skills/creator-intake-planner"


class IntakeSkillIntegrationTests(unittest.TestCase):
    def test_authoritative_skill_exposes_explicit_workflow_modes(self) -> None:
        text = (AUTHORITATIVE / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "creator-intake:approve",
            "scaffold-only",
            "handoff-to-execution",
            "state-registration proposal",
            "Mode-to-Resource Map",
            "creator-workspace-manager",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_required_runtime_assets_and_references_exist_in_both_sources(self) -> None:
        relatives = (
            "assets/project-template.json",
            "assets/activity-ledger-event-template.json",
            "assets/decisions-template.md",
            "assets/project-readme-template.md",
            "assets/state-registration-proposal-template.json",
            "assets/execution-handoff-template.json",
            "references/intake-artifact-contract.md",
            "references/approval-workflow.md",
            "references/scaffolding-workflow.md",
            "references/handoff-workflow.md",
            "references/state-registration-proposal.md",
        )
        for relative in relatives:
            with self.subTest(relative=relative):
                self.assertEqual((AUTHORITATIVE / relative).read_bytes(), (PLUGIN / relative).read_bytes())


if __name__ == "__main__":
    unittest.main()
