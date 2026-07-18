from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE = ROOT / ".agents/skills/creator-workspace-manager"
PACKAGED = ROOT / "plugin/creator-toolchain/skills/creator-workspace-manager"


class WorkspaceManagerSkillIntegrationTests(unittest.TestCase):
    def test_skill_exposes_deterministic_modes_and_boundaries(self) -> None:
        text = (AUTHORITATIVE / "SKILL.md").read_text(encoding="utf-8")
        for concept in (
            "creator-workspace:proposal list",
            "creator-workspace:proposal status",
            "creator-workspace:proposal preview",
            "creator-workspace:proposal apply",
            "creator-workspace:maintenance-review",
            "creator-workspace:archive plan",
            "creator-workspace:archive apply",
            "Mode-to-Resource Map",
            "config/surface-registry.json",
            "Do not implement backlog features",
            "Do not mutate `.creator/rules.json`",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, text)

    def test_workspace_resources_are_complete_and_packaged(self) -> None:
        required = {
            "references/state-surfaces.md",
            "references/health-maintenance.md",
            "references/proposal-lifecycle.md",
            "references/maintenance-archive.md",
            "references/session-insight-rule-bridge.md",
            "assets/surface-template.json",
            "assets/health-report-template.json",
            "assets/maintenance-review-template.md",
            "assets/archive-proposal-template.json",
            "assets/reconciliation-receipt-template.json",
        }
        for relative in required | {"SKILL.md"}:
            with self.subTest(path=relative):
                source = AUTHORITATIVE / relative
                packaged = PACKAGED / relative
                self.assertTrue(source.is_file())
                self.assertTrue(packaged.is_file())
                self.assertEqual(source.read_bytes(), packaged.read_bytes())

    def test_surface_template_uses_current_schema_and_privacy(self) -> None:
        value = json.loads((AUTHORITATIVE / "assets/surface-template.json").read_text(encoding="utf-8"))
        self.assertEqual(value["schema_version"], "0.4.0")
        self.assertIn(value["privacy_class"], {"publishable_template", "repository_workflow_state", "private", "repository_contract"})
        self.assertNotEqual(value["privacy_class"], "local_private")
        for field in ("surface_id", "created_at", "updated_at", "status", "records"):
            self.assertIn(field, value)


if __name__ == "__main__":
    unittest.main()
