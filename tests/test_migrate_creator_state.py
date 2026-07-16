from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.creator_state_store import STATE_FILES
from scripts.migrate_creator_state import MigrationError, build_migration_plan, migrate_value


class MigrateCreatorStateTests(unittest.TestCase):
    def test_migrate_value_updates_schema_and_timestamps(self) -> None:
        migrated = migrate_value(".creator/projects.json", {"schema_version":"0.3.0","privacy_class":"repository_workflow_state","projects":[]}, timestamp="2026-07-16T00:00:00Z")
        self.assertEqual(migrated["schema_version"], "0.4.0")
        self.assertEqual(migrated["created_at"], "2026-07-16T00:00:00Z")
        self.assertEqual(migrated["updated_at"], "2026-07-16T00:00:00Z")

    def test_non_030_source_is_rejected(self) -> None:
        with self.assertRaises(MigrationError):
            migrate_value(".creator/projects.json", {"schema_version":"0.4.0"}, timestamp="now")

    def test_plan_covers_all_state_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".creator").mkdir()
            for relative in STATE_FILES:
                value = {"schema_version":"0.3.0","privacy_class":"repository_workflow_state"}
                (root / relative).write_text(json.dumps(value), encoding="utf-8")
            plan = build_migration_plan(root)
            self.assertEqual(len(plan["files"]), len(STATE_FILES))
            self.assertFalse(plan["write_enabled"])


if __name__ == "__main__":
    unittest.main()
