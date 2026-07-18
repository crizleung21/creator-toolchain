from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_creator_workspace import bootstrap
from scripts.creator_workspace_maintenance import (
    MaintenanceError,
    apply_archive,
    archive_status,
    create_archive_proposal,
    maintenance_review,
)

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = "2026-07-18T06:50:00Z"


class CreatorWorkspaceMaintenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        bootstrap(self.root, write=True)

    def test_maintenance_review_is_read_only_and_surfaces_stale_plan(self) -> None:
        plan_dir = self.root / ".creator/plans/old"
        plan_dir.mkdir(parents=True)
        (plan_dir / "project.json").write_text(
            json.dumps({"stage": "planned", "updated_at": "2026-01-01T00:00:00Z"}) + "\n",
            encoding="utf-8",
        )
        before = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in (self.root / ".creator").rglob("*") if path.is_file()}
        report = maintenance_review(
            self.root,
            generated_at=TIMESTAMP,
            stale_plan_days=30,
            include_repository_checks=False,
            schema_root=ROOT,
        )
        after = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in (self.root / ".creator").rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(report["health_level"], "amber")
        self.assertEqual(report["archive_candidates"][0]["path"], ".creator/plans/old")

    def test_archive_is_two_step_and_non_destructive_until_apply(self) -> None:
        target = self.root / ".creator/tmp/note.txt"
        target.parent.mkdir(parents=True)
        target.write_text("archive me\n", encoding="utf-8")
        proposal = create_archive_proposal(
            self.root,
            ".creator/tmp/note.txt",
            actor="tester",
            reason="obsolete fixture",
            timestamp=TIMESTAMP,
            schema_root=ROOT,
        )
        self.assertTrue(target.is_file())
        self.assertEqual(archive_status(self.root, proposal["proposal_path"], schema_root=ROOT)["lifecycle_status"], "staged")
        result = apply_archive(
            self.root,
            proposal["proposal_path"],
            actor="tester",
            confirm=proposal["proposal_id"],
            timestamp=TIMESTAMP,
            schema_root=ROOT,
            include_repository_checks=False,
        )
        self.assertFalse(target.exists())
        archived = self.root / result["archive_path"]
        self.assertEqual(archived.read_text(encoding="utf-8"), "archive me\n")
        self.assertEqual(archive_status(self.root, proposal["proposal_path"], schema_root=ROOT)["lifecycle_status"], "archived")
        self.assertTrue((self.root / result["receipt_path"]).is_file())

    def test_archive_requires_exact_confirmation(self) -> None:
        target = self.root / ".creator/tmp/note.txt"
        target.parent.mkdir(parents=True)
        target.write_text("keep\n", encoding="utf-8")
        proposal = create_archive_proposal(self.root, ".creator/tmp/note.txt", actor="tester", reason="cleanup", timestamp=TIMESTAMP, schema_root=ROOT)
        with self.assertRaises(MaintenanceError):
            apply_archive(
                self.root,
                proposal["proposal_path"],
                actor="tester",
                confirm="wrong-token",
                timestamp=TIMESTAMP,
                schema_root=ROOT,
                include_repository_checks=False,
            )
        self.assertTrue(target.is_file())

    def test_root_state_surface_cannot_be_archived(self) -> None:
        with self.assertRaises(MaintenanceError):
            create_archive_proposal(self.root, ".creator/projects.json", actor="tester", reason="unsafe", timestamp=TIMESTAMP, schema_root=ROOT)

    def test_referenced_plan_cannot_be_archived(self) -> None:
        plan_dir = self.root / ".creator/plans/demo"
        plan_dir.mkdir(parents=True)
        (plan_dir / "PLANNING.md").write_text("# Plan\n", encoding="utf-8")
        projects_path = self.root / ".creator/projects.json"
        projects = json.loads(projects_path.read_text(encoding="utf-8"))
        projects["projects"].append(
            {
                "project_id": "PROJECT-AAAAAAAA",
                "title": "Demo",
                "project_type": "utility",
                "status": "approved",
                "plan_path": ".creator/plans/demo/PLANNING.md",
                "last_summary": None,
                "created_at": TIMESTAMP,
                "updated_at": TIMESTAMP,
            }
        )
        projects["updated_at"] = TIMESTAMP
        projects_path.write_text(json.dumps(projects, indent=2) + "\n", encoding="utf-8")
        with self.assertRaises(MaintenanceError):
            create_archive_proposal(self.root, ".creator/plans/demo", actor="tester", reason="still active", timestamp=TIMESTAMP, schema_root=ROOT)

    def test_injected_failure_restores_original_path_and_bytes(self) -> None:
        target = self.root / ".creator/tmp/note.txt"
        target.parent.mkdir(parents=True)
        target.write_text("restore me\n", encoding="utf-8")
        proposal = create_archive_proposal(self.root, ".creator/tmp/note.txt", actor="tester", reason="rollback test", timestamp=TIMESTAMP, schema_root=ROOT)
        state_before = (self.root / ".creator/state.json").read_bytes()
        with self.assertRaises(MaintenanceError):
            apply_archive(
                self.root,
                proposal["proposal_path"],
                actor="tester",
                confirm=proposal["proposal_id"],
                timestamp=TIMESTAMP,
                schema_root=ROOT,
                include_repository_checks=False,
                fail_after_move=True,
            )
        self.assertEqual(target.read_text(encoding="utf-8"), "restore me\n")
        self.assertEqual((self.root / ".creator/state.json").read_bytes(), state_before)
        self.assertFalse((self.root / f".creator/maintenance/archive-receipts/{proposal['proposal_id']}.json").exists())


if __name__ == "__main__":
    unittest.main()
