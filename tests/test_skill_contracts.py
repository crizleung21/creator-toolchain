from __future__ import annotations

import unittest
from pathlib import Path

from scripts.sync_plugin_skills import SKILLS, synchronize


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills"
PLUGIN_SKILL_ROOT = ROOT / "plugin/creator-toolchain/skills"


REQUIRED_CONCEPTS = {
    "creator-seed-incubator": [
        "creator-seed:ideate",
        "SEED-STATE.md",
        "Planning Quality Gate",
        "graduate",
        "launch",
    ],
    "creator-paul-loop": [
        "PLAN",
        "APPLY",
        "QUALIFY",
        "UNIFY",
        "DONE_WITH_CONCERNS",
        "activity_ledger.jsonl",
    ],
    "creator-base-workspace": [
        ".creator/workspace.json",
        "creator-base:pulse",
        "creator-base:groom",
        "PSMM",
    ],
    "creator-rule-router": [
        "GLOBAL",
        "stage-proposal",
        "recall",
        "exclude",
        "audit-conflicts",
    ],
    "creator-skillsmith-factory": [
        "discover",
        "scaffold",
        "distill",
        "score",
        "audit",
    ],
    "creator-aegis-audit": [
        "Phase 0",
        "Phase 8",
        "Layer A",
        "Layer B",
        "Layer C",
        "does not directly mutate",
    ],
}


class SkillContractTests(unittest.TestCase):
    def test_capability_qa_documents_exist(self) -> None:
        self.assertTrue((ROOT / "docs/qa/capability-matrix.md").is_file())
        self.assertTrue((ROOT / "docs/qa/skill-contract-tests.md").is_file())

    def test_capability_matrix_covers_all_source_tools(self) -> None:
        text = (ROOT / "docs/qa/capability-matrix.md").read_text(encoding="utf-8")
        for source in ["SEED", "PAUL", "BASE", "CARL", "Skillsmith", "AEGIS"]:
            with self.subTest(source=source):
                self.assertIn(source, text)

    def test_authoritative_skills_express_required_contracts(self) -> None:
        for skill, concepts in REQUIRED_CONCEPTS.items():
            text = (SKILL_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            for concept in concepts:
                with self.subTest(skill=skill, concept=concept):
                    self.assertIn(concept, text)

    def test_all_thirteen_seed_types_have_three_reference_files(self) -> None:
        type_root = SKILL_ROOT / "creator-seed-incubator/references/types"
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


if __name__ == "__main__":
    unittest.main()
