from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_creator_workspace import bootstrap
from scripts.creator_health_check import calculate_health, write_health

ROOT = Path(__file__).resolve().parents[1]
TS = "2026-07-18T06:00:00Z"


class CreatorHealthCheckTests(unittest.TestCase):
    def test_fresh_workspace_is_green_without_repository_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            report = calculate_health(root, calculated_at=TS, include_repository_checks=False, schema_root=ROOT)
            self.assertEqual(report["level"], "green")
            self.assertEqual(report["score"], 0)
            self.assertEqual(report["signals"], [])

    def test_unknown_active_project_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            state_path = root / ".creator/state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["active_projects"] = ["PROJECT-AAAAAAAA"]
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            report = calculate_health(root, calculated_at=TS, include_repository_checks=False, schema_root=ROOT)
            self.assertEqual(report["level"], "red")
            self.assertTrue(any(item["signal_id"] == "WORKSPACE_CONTRACT_FAILURE" for item in report["signals"]))

    def test_stale_plan_is_amber(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            plan = root / ".creator/plans/demo/project.json"
            plan.parent.mkdir(parents=True)
            plan.write_text(json.dumps({"stage": "planned", "updated_at": "2026-05-01T00:00:00Z"}), encoding="utf-8")
            report = calculate_health(root, calculated_at=TS, stale_plan_days=30, include_repository_checks=False, schema_root=ROOT)
            self.assertEqual(report["level"], "amber")
            self.assertTrue(any(item["signal_id"] == "STALE_PLAN" for item in report["signals"]))

    def test_write_health_updates_state_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            report = calculate_health(root, calculated_at=TS, include_repository_checks=False, schema_root=ROOT)
            write_health(root, report, schema_root=ROOT)
            stored = json.loads((root / ".creator/health/health-report.json").read_text(encoding="utf-8"))
            state = json.loads((root / ".creator/state.json").read_text(encoding="utf-8"))
            self.assertEqual(stored, report)
            self.assertEqual(state["last_health_check"], TS)
            self.assertEqual(state["state_divergence"]["level"], "green")
            self.assertIn("health-report.json", state["state_divergence"]["notes"])


if __name__ == "__main__":
    unittest.main()
