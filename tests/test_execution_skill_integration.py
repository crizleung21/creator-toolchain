from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.sync_plugin_skills import synchronize

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".agents/skills/creator-execution-cycle"
MIRROR = ROOT / "plugin/creator-toolchain/skills/creator-execution-cycle"


class ExecutionSkillIntegrationTests(unittest.TestCase):
    def test_execution_skill_exposes_complete_runtime_contract(self) -> None:
        text = (SOURCE / "SKILL.md").read_text(encoding="utf-8")
        for concept in (
            "creator-execution:plan",
            "creator-execution:recover",
            "Mode-to-Resource Map",
            "scripts/creator_execution_lifecycle.py",
            "scripts/creator_execution_closure.py",
            "RECONCILIATION-{seq}.md",
            "SUMMARY-{seq}.md",
            "state-update-proposal.json",
            "orphan-plan",
            "interrupted-execution",
            "failed-verification",
            "blocked-task",
            "state-divergence",
            "scope-creep",
            "incomplete-reconciliation",
            "creator-workspace-manager",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, text)

    def test_deprecated_recovery_terms_are_absent(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [
                SOURCE / "SKILL.md",
                SOURCE / "references/execution-lifecycle.md",
                SOURCE / "references/recovery-workflows.md",
            ]
        )
        self.assertNotIn("Failed Qualify Recovery", combined)
        self.assertNotIn("return to Apply", combined)

    def test_required_execution_resources_exist(self) -> None:
        for relative in (
            "references/execution-lifecycle.md",
            "references/recovery-workflows.md",
            "references/closure-contract.md",
            "references/state-update-proposal.md",
            "references/acceptance-driven-work.md",
            "references/escalation-statuses.md",
            "assets/plan-template.md",
            "assets/reconciliation-template.md",
            "assets/summary-template.md",
            "assets/blocker-template.md",
            "assets/recovery-plan-template.md",
            "assets/reconciliation-recovery-template.md",
            "assets/state-update-proposal-template.json",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((SOURCE / relative).is_file())

    def test_state_update_template_preserves_ownership_boundary(self) -> None:
        value = json.loads(
            (SOURCE / "assets/state-update-proposal-template.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(value["target_surface"], ".creator/projects.json")
        self.assertEqual(value["owner_skill"], "creator-workspace-manager")
        self.assertEqual(value["requested_by"], "creator-execution-cycle")
        self.assertEqual(value["status"], "staged")

    def test_plugin_mirror_is_byte_equivalent(self) -> None:
        self.assertEqual(
            synchronize(
                ROOT / ".agents/skills",
                ROOT / "plugin/creator-toolchain/skills",
                write=False,
            ),
            [],
        )
        for relative in (
            "SKILL.md",
            "references/closure-contract.md",
            "references/recovery-workflows.md",
            "assets/state-update-proposal-template.json",
        ):
            self.assertEqual(
                (SOURCE / relative).read_bytes(),
                (MIRROR / relative).read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
