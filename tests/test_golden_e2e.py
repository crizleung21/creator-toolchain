from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_golden_e2e import GoldenE2EError, run_golden_e2e

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "a" * 40


class GoldenE2ETests(unittest.TestCase):
    def test_writable_golden_workflow_closes_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            report = run_golden_e2e(workspace, source_root=ROOT, commit_sha=COMMIT)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["fixture_id"], "creator-asset-naming-checker")
            self.assertEqual(report["final_health"], {"level": "green", "score": 0, "signal_count": 0})
            self.assertEqual(report["final_validation_findings"], [])
            self.assertIn("zh-hant", report["rule_preflight"]["matched_domains"])
            self.assertTrue(report["utility"]["deterministic"])
            self.assertGreaterEqual(report["utility"]["invalid_count"], 2)
            project = json.loads((workspace / ".creator/projects.json").read_text(encoding="utf-8"))
            record = next(item for item in project["projects"] if item["project_id"] == report["project_id"])
            self.assertEqual(record["status"], "done")
            self.assertTrue((workspace / f".creator/audits/{report['audit']['audit_id']}/handoffs/{report['audit']['handoff_id']}.json").is_file())

    def test_two_workspaces_produce_identical_utility_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first_root = Path(first_dir) / "workspace"
            second_root = Path(second_dir) / "workspace"
            first = run_golden_e2e(first_root, source_root=ROOT, commit_sha=COMMIT)
            second = run_golden_e2e(second_root, source_root=ROOT, commit_sha=COMMIT)
            self.assertEqual(first["project_id"], second["project_id"])
            self.assertEqual(first["utility"], second["utility"])
            self.assertEqual((first_root / "evidence/naming-report.json").read_bytes(), (second_root / "evidence/naming-report.json").read_bytes())

    def test_nonempty_workspace_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            sentinel = workspace / "sentinel.txt"
            sentinel.write_text("unchanged\n", encoding="utf-8")
            with self.assertRaises(GoldenE2EError):
                run_golden_e2e(workspace, source_root=ROOT, commit_sha=COMMIT)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "unchanged\n")


if __name__ == "__main__":
    unittest.main()
