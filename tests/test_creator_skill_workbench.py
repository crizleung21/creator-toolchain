from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.creator_skill_workbench import score_all, score_skill

ROOT = Path(__file__).resolve().parents[1]


COMPLETE_SKILL = """---
name: creator-demo
description: Create and audit a focused creator demo skill for a bounded workflow, including explicit trigger and output scope.
---

# creator-demo

## Workflows

- discover
- scaffold
- verify

## Required Output

Produce a deterministic report and verification evidence.

## State Surfaces

Read `.creator/projects.json`. Do not mutate state or files owned by another workflow.

## Guardrails

- Do not execute product work.
- Do not hide missing evidence.
- Never overwrite another skill.

## Acceptance Tests

Acceptance tests must verify trigger routing, reference integrity, and state safety.

See `references/workflow.md` and use `assets/report-template.md`.
"""


class CreatorSkillWorkbenchTests(unittest.TestCase):
    def make_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        (root / ".agents/skills/creator-demo/references").mkdir(parents=True)
        (root / ".agents/skills/creator-demo/assets").mkdir(parents=True)
        (root / "tests").mkdir()
        (root / ".agents/skills/creator-demo/SKILL.md").write_text(COMPLETE_SKILL, encoding="utf-8")
        (root / ".agents/skills/creator-demo/references/workflow.md").write_text("# Workflow\n", encoding="utf-8")
        (root / ".agents/skills/creator-demo/assets/report-template.md").write_text("# Report\n", encoding="utf-8")
        (root / "tests/test_creator_demo.py").write_text("# creator-demo acceptance test\n", encoding="utf-8")
        return tempdir, root

    def test_complete_skill_scores_100(self) -> None:
        _, root = self.make_root()
        report = score_skill(root, ".agents/skills/creator-demo", schema_root=ROOT)
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["status"], "compliant")
        self.assertEqual(report["deductions"], [])

    def test_score_is_deterministic(self) -> None:
        first = score_skill(ROOT, ".agents/skills/creator-skill-workbench", schema_root=ROOT)
        second = score_skill(ROOT, ".agents/skills/creator-skill-workbench", schema_root=ROOT)
        self.assertEqual(first, second)
        self.assertEqual(sum(item["weight"] for item in first["dimensions"]), 100)
        self.assertEqual(first["score"], sum(item["awarded"] for item in first["dimensions"]))

    def test_missing_reference_creates_evidence_backed_deduction(self) -> None:
        _, root = self.make_root()
        (root / ".agents/skills/creator-demo/references/workflow.md").unlink()
        report = score_skill(root, ".agents/skills/creator-demo", schema_root=ROOT)
        deduction = next(item for item in report["deductions"] if item["check_id"] == "REFERENCE_EXISTS")
        self.assertIn("workflow.md", deduction["evidence"])
        self.assertLess(report["score"], 100)

    def test_duplicate_name_reduces_naming_score(self) -> None:
        _, root = self.make_root()
        duplicate = root / ".agents/skills/creator-demo-copy"
        duplicate.mkdir()
        duplicate.joinpath("SKILL.md").write_text(COMPLETE_SKILL, encoding="utf-8")
        report = score_skill(root, ".agents/skills/creator-demo", schema_root=ROOT)
        self.assertTrue(any(item["check_id"] == "NAME_UNIQUE" for item in report["deductions"]))

    def test_score_all_returns_each_skill_once(self) -> None:
        _, root = self.make_root()
        reports = score_all(root, schema_root=ROOT)
        self.assertEqual([item["skill_name"] for item in reports], ["creator-demo"])


if __name__ == "__main__":
    unittest.main()
