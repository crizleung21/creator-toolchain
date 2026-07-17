from __future__ import annotations
import shutil,tempfile,unittest
from pathlib import Path
from scripts.creator_state_store import STATE_FILES,validate_workspace
from scripts.migrate_creator_state import MigrationError,build_migration_plan,migrate_workspace,restore_backup
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/state-v0.3.0'
TS='2026-07-17T16:47:46Z'
class MigrationTests(unittest.TestCase):
    def workspace(self):
        td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); root=Path(td.name); shutil.copytree(FIXTURE,root,dirs_exist_ok=True); return root
    def bytes(self,root): return {r:(root/r).read_bytes() for r in STATE_FILES}
    def test_plan_covers_all_files(self):
        plan=build_migration_plan(self.workspace(),timestamp=TS)
        self.assertEqual(len(plan['files']),10); self.assertTrue(plan['write_enabled'])
    def test_transactional_migration_validates(self):
        root=self.workspace(); backup=root.parent/(root.name+'-backup')
        report=migrate_workspace(root,backup,timestamp=TS)
        self.assertEqual(report['status'],'PASS'); self.assertEqual(validate_workspace(root),[])
        self.assertTrue(all((root/r).read_text().find('"schema_version": "0.4.0"')>=0 for r in STATE_FILES))
    def test_explicit_rollback_is_byte_equivalent(self):
        root=self.workspace(); original=self.bytes(root); backup=root.parent/(root.name+'-backup')
        migrate_workspace(root,backup,timestamp=TS); restore_backup(root,backup)
        self.assertEqual(self.bytes(root),original)
    def test_injected_failure_restores_all_bytes(self):
        root=self.workspace(); original=self.bytes(root); backup=root.parent/(root.name+'-backup')
        with self.assertRaises(MigrationError): migrate_workspace(root,backup,timestamp=TS,fail_after=4)
        self.assertEqual(self.bytes(root),original)
    def test_write_requires_clean_backup_destination(self):
        root=self.workspace(); backup=root.parent/(root.name+'-backup'); backup.mkdir()
        with self.assertRaises(MigrationError): migrate_workspace(root,backup,timestamp=TS)
if __name__=='__main__': unittest.main()
