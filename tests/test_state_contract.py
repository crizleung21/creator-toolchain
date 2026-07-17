from __future__ import annotations
import json,shutil,tempfile,unittest
from pathlib import Path
from scripts.creator_state_store import STATE_FILES,SURFACE_REGISTRY,validate_workspace
from scripts.migrate_creator_state import migrate_workspace
ROOT=Path(__file__).resolve().parents[1]; FIXTURE=ROOT/'tests/fixtures/state-v0.3.0'; TS='2026-07-17T16:47:46Z'
class StateContractTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup); self.root=Path(self.t.name); shutil.copytree(FIXTURE,self.root,dirs_exist_ok=True); migrate_workspace(self.root,self.root.parent/(self.root.name+'-backup'),timestamp=TS)
    def read(self,name): return json.loads((self.root/'.creator'/name).read_text())
    def write(self,name,value): (self.root/'.creator'/name).write_text(json.dumps(value,indent=2)+"\n")
    def test_all_state_files_use_schema_040(self):
        self.assertEqual(validate_workspace(self.root),[])
        self.assertTrue(all(self.read(Path(r).name)['schema_version']=='0.4.0' for r in STATE_FILES))
    def test_missing_timestamp_is_rejected(self):
        v=self.read('projects.json'); v.pop('updated_at'); self.write('projects.json',v)
        self.assertTrue(any('updated_at' in f for f in validate_workspace(self.root)))
    def test_surface_registry_must_match_contract(self):
        v=self.read('surfaces.json'); v['surfaces'][0]['mutable']=False; self.write('surfaces.json',v)
        self.assertTrue(any('surface registry mismatch' in f for f in validate_workspace(self.root)))
    def test_rule_domain_requires_scope_owner_and_timestamp(self):
        v=self.read('rules.json'); v['domains'][0].pop('scope'); self.write('rules.json',v)
        self.assertTrue(any('scope' in f for f in validate_workspace(self.root)))
    def test_unknown_decision_reference_is_rejected(self):
        v=self.read('rules.json'); v['domains'][0]['decision_refs']=['DEC-999']; self.write('rules.json',v)
        self.assertTrue(any('unknown decision refs' in f for f in validate_workspace(self.root)))
    def test_unknown_active_project_is_rejected(self):
        v=self.read('state.json'); v['active_projects']=['missing']; self.write('state.json',v)
        self.assertTrue(any('unknown state project IDs' in f for f in validate_workspace(self.root)))
if __name__=='__main__': unittest.main()
