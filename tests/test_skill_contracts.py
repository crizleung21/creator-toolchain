from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.sync_plugin_skills import SKILLS, synchronize


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills"
PLUGIN_SKILL_ROOT = ROOT / "plugin/creator-toolchain/skills"


REQUIRED_CONCEPTS = {
    "creator-intake-planner": [
        "creator-intake:start",
        "INTAKE-STATE.md",
        "Planning Quality Gate",
        "scaffold",
        "handoff",
    ],
    "creator-execution-cycle": [
        "PLAN",
        "EXECUTE",
        "VERIFY",
        "RECONCILE",
        "DONE_WITH_CONCERNS",
        "activity_ledger.jsonl",
    ],
    "creator-workspace-manager": [
        ".creator/workspace.json",
        "creator-workspace:health-check",
        "creator-workspace:maintenance-review",
        "Session Insights",
    ],
    "creator-rule-router": [
        "GLOBAL",
        "stage-proposal",
        "recall",
        "exclude",
        "audit-conflicts",
    ],
    "creator-skill-workbench": [
        "discover",
        "scaffold",
        "distill",
        "score",
        "audit",
    ],
    "creator-evidence-audit": [
        "Phase 0",
        "Phase 8",
        "Findings",
        "Remediation Guidance",
        "Execution Handoff",
        "does not directly mutate",
    ],
}


class SkillContractTests(unittest.TestCase):
    def test_capability_qa_documents_exist(self) -> None:
        self.assertTrue((ROOT / "docs/qa/capability-matrix.md").is_file())
        self.assertTrue((ROOT / "docs/qa/skill-contract-tests.md").is_file())

    def test_capability_matrix_covers_all_creator_capabilities(self) -> None:
        text = (ROOT / "docs/qa/capability-matrix.md").read_text(encoding="utf-8")
        for capability in [
            "Intake",
            "Execution Cycle",
            "Workspace State",
            "Rule Governance",
            "Skill Workbench",
            "Evidence Audit",
        ]:
            with self.subTest(capability=capability):
                self.assertIn(capability, text)

    def test_authoritative_skills_express_required_contracts(self) -> None:
        for skill, concepts in REQUIRED_CONCEPTS.items():
            skill_file = SKILL_ROOT / skill / "SKILL.md"
            self.assertTrue(skill_file.is_file(), skill)
            text = skill_file.read_text(encoding="utf-8")
            for concept in concepts:
                with self.subTest(skill=skill, concept=concept):
                    self.assertIn(concept, text)

    def test_all_thirteen_project_types_have_three_reference_files(self) -> None:
        type_root = SKILL_ROOT / "creator-intake-planner/references/types"
        self.assertTrue(type_root.is_dir())
        type_dirs = sorted(path for path in type_root.iterdir() if path.is_dir())
        self.assertEqual(len(type_dirs), 13)
        for type_dir in type_dirs:
            for filename in ["guide.md", "config.md", "skill-loadout.md"]:
                with self.subTest(type_id=type_dir.name, filename=filename):
                    self.assertTrue((type_dir / filename).is_file())

    def test_plugin_mirror_matches_authoritative_skills(self) -> None:
        self.assertEqual(
            synchronize(SKILL_ROOT, PLUGIN_SKILL_ROOT, write=False),
            [],
        )

    def test_exactly_seven_authoritative_skills_exist(self) -> None:
        found = sorted(path.name for path in SKILL_ROOT.iterdir() if (path / "SKILL.md").is_file())
        self.assertEqual(found, sorted(SKILLS))

    def test_plugin_uses_creator_native_draft_version(self) -> None:
        manifest_path = ROOT / "plugin/creator-toolchain/.codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "1.0.0-draft.1")


if __name__ == "__main__":
    unittest.main()
