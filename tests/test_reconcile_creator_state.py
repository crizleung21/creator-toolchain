from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_creator_workspace import bootstrap
from scripts.reconcile_creator_state import ReconciliationError, apply_reconciliation, preview_reconciliation

ROOT = Path(__file__).resolve().parents[1]
TS = "2026-07-18T06:00:00Z"
PROJECT_ID = "PROJECT-AAAAAAAA"
PROPOSAL_ID = "PROPOSAL-AAAAAAAA"


class ReconcileCreatorStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        bootstrap(self.root, write=True)
        plan_dir = self.root / ".creator/plans/demo"
        plan_dir.mkdir(parents=True)
        names = ["PLANNING.md", "project.json", "INTAKE-STATE.md", "HANDOFF.md"]
        for name in names:
            (plan_dir / name).write_text("# evidence\n", encoding="utf-8")
        self.proposal_relative = f".creator/state-proposals/{PROJECT_ID}.json"
        proposal_path = self.root / self.proposal_relative
        proposal_path.parent.mkdir(parents=True)
        proposal = {
            "schema_version": "1.0.0",
            "proposal_id": PROPOSAL_ID,
            "operation": "register-project",
            "status": "staged",
            "target_surface": ".creator/projects.json",
            "owner_skill": "creator-workspace-manager",
            "requested_by": "creator-intake-planner",
            "source_plan": ".creator/plans/demo/PLANNING.md",
            "proposal_path": self.proposal_relative,
            "project": {
                "project_id": PROJECT_ID,
                "title": "Demo",
                "project_type": "utility",
                "status": "approved",
                "plan_path": ".creator/plans/demo/PLANNING.md",
                "last_summary": None,
                "created_at": TS,
                "updated_at": TS
            },
            "evidence_paths": [f".creator/plans/demo/{name}" for name in names],
            "created_at": TS,
            "updated_at": TS
        }
        proposal_path.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")

    def _projects_bytes(self) -> bytes:
        return (self.root / ".creator/projects.json").read_bytes()

    def test_preview_is_read_only(self) -> None:
        before = self._projects_bytes()
        preview = preview_reconciliation(self.root, self.proposal_relative, timestamp=TS, schema_root=ROOT)
        self.assertEqual(preview["action"], "add")
        self.assertTrue(preview["changed"])
        self.assertEqual(before, self._projects_bytes())
        self.assertFalse((self.root / preview["receipt_path"]).exists())

    def test_apply_registers_project_and_writes_receipt(self) -> None:
        result = apply_reconciliation(self.root, self.proposal_relative, actor="tester", timestamp=TS, schema_root=ROOT, include_repository_checks=False)
        projects = json.loads((self.root / ".creator/projects.json").read_text(encoding="utf-8"))
        self.assertEqual([item["project_id"] for item in projects["projects"]], [PROJECT_ID])
        self.assertEqual(result["status"], "applied")
        self.assertTrue((self.root / result["receipt_path"]).is_file())
        self.assertTrue((self.root / ".creator/reconciliation/activity_ledger.jsonl").is_file())
        self.assertTrue((self.root / ".creator/health/health-report.json").is_file())

    def test_wrong_owner_is_rejected_without_writes(self) -> None:
        proposal_path = self.root / self.proposal_relative
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        proposal["owner_skill"] = "creator-intake-planner"
        proposal_path.write_text(json.dumps(proposal), encoding="utf-8")
        before = self._projects_bytes()
        with self.assertRaises(ReconciliationError):
            preview_reconciliation(self.root, self.proposal_relative, timestamp=TS, schema_root=ROOT)
        self.assertEqual(before, self._projects_bytes())

    def test_injected_failure_restores_projects_byte_equivalent(self) -> None:
        before = self._projects_bytes()
        with self.assertRaises(ReconciliationError):
            apply_reconciliation(self.root, self.proposal_relative, actor="tester", timestamp=TS, schema_root=ROOT, include_repository_checks=False, fail_after_projects=True)
        self.assertEqual(before, self._projects_bytes())
        self.assertFalse((self.root / f".creator/reconciliation/{PROPOSAL_ID}.json").exists())


if __name__ == "__main__":
    unittest.main()
