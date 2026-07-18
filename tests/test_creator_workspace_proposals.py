from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_creator_workspace import bootstrap
from scripts.creator_workspace_proposals import discover_proposals, proposal_status

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = "2026-07-18T06:40:00Z"
PROJECT_ID = "PROJECT-AAAAAAAA"
PROPOSAL_ID = "PROPOSAL-AAAAAAAA"


class CreatorWorkspaceProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        bootstrap(self.root, write=True)
        plan_dir = self.root / ".creator/plans/demo"
        plan_dir.mkdir(parents=True)
        for name in ("PLANNING.md", "HANDOFF.md", "DECISIONS.md", "OPEN-QUESTIONS.md"):
            (plan_dir / name).write_text(f"# {name}\n", encoding="utf-8")
        self.proposal_relative = f".creator/state-proposals/{PROJECT_ID}.json"
        self.proposal_path = self.root / self.proposal_relative
        self.proposal_path.parent.mkdir(parents=True)
        self.proposal = {
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
                "created_at": TIMESTAMP,
                "updated_at": TIMESTAMP,
            },
            "evidence_paths": [
                ".creator/plans/demo/PLANNING.md",
                ".creator/plans/demo/HANDOFF.md",
                ".creator/plans/demo/DECISIONS.md",
                ".creator/plans/demo/OPEN-QUESTIONS.md",
            ],
            "created_at": TIMESTAMP,
            "updated_at": TIMESTAMP,
        }
        self.proposal_path.write_text(json.dumps(self.proposal, indent=2) + "\n", encoding="utf-8")

    def test_discovery_reports_staged_proposal(self) -> None:
        result = discover_proposals(self.root, schema_root=ROOT)
        self.assertEqual(result["counts"], {"staged": 1, "applied": 0, "invalid": 0})
        self.assertEqual(result["proposals"][0]["proposal_id"], PROPOSAL_ID)
        self.assertEqual(result["proposals"][0]["lifecycle_status"], "staged")

    def test_status_is_read_only(self) -> None:
        before = self.proposal_path.read_bytes()
        status = proposal_status(self.root, self.proposal_relative, schema_root=ROOT)
        self.assertEqual(status["lifecycle_status"], "staged")
        self.assertEqual(self.proposal_path.read_bytes(), before)

    def test_valid_receipt_changes_derived_status_without_mutating_proposal(self) -> None:
        before = self.proposal_path.read_bytes()
        receipt_path = self.root / f".creator/reconciliation/{PROPOSAL_ID}.json"
        receipt_path.parent.mkdir(parents=True)
        receipt = {
            "schema_version": "1.0.0",
            "proposal_id": PROPOSAL_ID,
            "operation": "register-project",
            "status": "applied",
            "target_surface": ".creator/projects.json",
            "project_id": PROJECT_ID,
            "before_sha256": "a" * 64,
            "after_sha256": "b" * 64,
            "applied_by": "tester",
            "applied_at": TIMESTAMP,
            "proposal_path": self.proposal_relative,
            "receipt_path": f".creator/reconciliation/{PROPOSAL_ID}.json",
            "health_report": ".creator/health/health-report.json",
        }
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        status = proposal_status(self.root, self.proposal_relative, schema_root=ROOT)
        self.assertEqual(status["lifecycle_status"], "applied")
        self.assertEqual(status["lifecycle_evidence"], receipt_path.relative_to(self.root).as_posix())
        self.assertEqual(self.proposal_path.read_bytes(), before)

    def test_duplicate_proposal_id_is_invalid(self) -> None:
        duplicate = self.root / f".creator/executions/{PROJECT_ID}/state-update-proposal.json"
        duplicate.parent.mkdir(parents=True)
        duplicate.write_text(json.dumps(self.proposal, indent=2) + "\n", encoding="utf-8")
        result = discover_proposals(self.root, schema_root=ROOT)
        self.assertEqual(result["counts"]["invalid"], 2)
        self.assertTrue(all("duplicate proposal_id" in record["finding"] for record in result["proposals"]))

    def test_invalid_owner_is_reported_without_throwing_list(self) -> None:
        value = dict(self.proposal)
        value["owner_skill"] = "creator-intake-planner"
        self.proposal_path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        result = discover_proposals(self.root, schema_root=ROOT)
        self.assertEqual(result["counts"]["invalid"], 1)
        self.assertIn("owner", result["proposals"][0]["finding"])


if __name__ == "__main__":
    unittest.main()
