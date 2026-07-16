from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_creator_workspace import bootstrap, planned_changes
from scripts.creator_state_store import STATE_FILES, validate_workspace


class BootstrapCreatorWorkspaceTests(unittest.TestCase):
    def test_bootstrap_creates_all_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            changes = bootstrap(root, workspace_id="demo", display_name="Demo", write=True)
            self.assertEqual(set(changes), set(STATE_FILES) | {".creator/ARCHITECTURE.md"})
            self.assertEqual(validate_workspace(root), [])

    def test_bootstrap_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            before = {relative: (root / relative).read_bytes() for relative in STATE_FILES}
            self.assertEqual(bootstrap(root, write=True), [])
            after = {relative: (root / relative).read_bytes() for relative in STATE_FILES}
            self.assertEqual(before, after)

    def test_existing_user_state_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            operator = root / ".creator/operator.json"
            text = operator.read_text(encoding="utf-8").replace("workspace-user", "criz")
            operator.write_text(text, encoding="utf-8")
            bootstrap(root, write=True)
            self.assertIn('"criz"', operator.read_text(encoding="utf-8"))

    def test_dry_run_lists_changes_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            changes = planned_changes(root)
            self.assertTrue(changes)
            self.assertFalse((root / ".creator").exists())


if __name__ == "__main__":
    unittest.main()
