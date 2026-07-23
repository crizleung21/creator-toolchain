from __future__ import annotations

import unittest
from pathlib import Path

from scripts.creator_skill_workbench import score_skill
from scripts.creator_workflow_router import route_request
from scripts.sync_plugin_skills import SKILLS

ROOT = Path(__file__).resolve().parents[1]


class Phase6SkillIntegrationTests(unittest.TestCase):
    def test_all_seven_skills_have_mode_to_resource_maps(self) -> None:
        self.assertEqual(len(SKILLS), 7)
        for skill in SKILLS:
            with self.subTest(skill=skill):
                text = (ROOT / ".agents/skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("## Mode-to-Resource Map", text)
                self.assertIn("| Mode | Required references | Optional assets | State surfaces |", text)

    def test_three_phase6_skills_are_compliant(self) -> None:
        for skill in ("creator-orchestrator", "creator-skill-workbench", "creator-evidence-audit"):
            with self.subTest(skill=skill):
                report = score_skill(ROOT, f".agents/skills/{skill}", schema_root=ROOT)
                self.assertGreaterEqual(report["score"], 90, report)
                self.assertEqual(report["status"], "compliant")

    def test_evidence_audit_route_has_available_runtime(self) -> None:
        result = route_request(ROOT, "Perform an evidence-first repository audit and issue findings.", schema_root=ROOT)
        self.assertEqual(result["primary_workflow"], "creator-evidence-audit")
        self.assertEqual(result["support_script"], "scripts/creator_evidence_audit.py")
        self.assertTrue(result["support_script_available"])

    def test_orchestrator_has_no_undefined_phase_workflow(self) -> None:
        text = (ROOT / ".agents/skills/creator-orchestrator/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("Phase 5 plugin workflow", text)
        self.assertIn("scripts/release_creator_toolchain.py", text)


if __name__ == "__main__":
    unittest.main()
