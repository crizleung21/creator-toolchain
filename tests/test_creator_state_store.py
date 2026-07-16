from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_creator_workspace import bootstrap
from scripts.creator_state_store import StateStoreError, load_json, surface_sha256, validate_surface, validate_workspace, write_surface


class CreatorStateStoreTests(unittest.TestCase):
    def test_bootstrapped_workspace_validates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            self.assertEqual(validate_workspace(root), [])

    def test_invalid_schema_is_rejected(self) -> None:
        value = {"schema_version":"0.3.0","owner_skill":"creator-workspace-manager","privacy_class":"repository_workflow_state","created_at":"now","updated_at":"now","projects":[]}
        self.assertTrue(validate_surface(".creator/projects.json", value))

    def test_optimistic_lock_blocks_stale_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            relative = ".creator/projects.json"
            path = root / relative
            value = load_json(path)
            current = surface_sha256(path)
            value["updated_at"] = "2026-07-16T01:00:00Z"
            write_surface(root, relative, value, expected_sha256=current)
            with self.assertRaises(StateStoreError):
                write_surface(root, relative, value, expected_sha256=current)

    def test_unsafe_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bootstrap(root, write=True)
            with self.assertRaises(StateStoreError):
                write_surface(root, "../escape.json", {})


if __name__ == "__main__":
    unittest.main()
