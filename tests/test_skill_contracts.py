from __future__ import annotations

import hashlib
import json
import unittest
import zipfile
from pathlib import Path

from scripts.sync_plugin_skills import SKILLS, synchronize
from scripts.versioning import read_version

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills"
PLUGIN_SKILL_ROOT = ROOT / "plugin/creator-toolchain/skills"

REQUIRED_CONCEPTS = {
    "creator-intake-planner": ["creator-intake:start", "INTAKE-STATE.md", "Planning Quality Gate", "scaffold", "handoff"],
    "creator-execution-cycle": ["PLAN", "EXECUTE", "VERIFY", "RECONCILE", "DONE_WITH_CONCERNS", "activity_ledger.jsonl"],
    "creator-workspace-manager": [".creator/workspace.json", "creator-workspace:health-check", "creator-workspace:maintenance-review", "Session Insights"],
    "creator-rule-router": ["GLOBAL", "stage-proposal", "recall", "exclude", "audit-conflicts"],
    "creator-skill-workbench": ["discover", "scaffold", "distill", "score", "audit"],
    "creator-evidence-audit": ["Phase 0", "Phase 8", "Findings", "Remediation Guidance", "Execution Handoff", "does not directly mutate"],
}


class SkillContractTests(unittest.TestCase):
    def test_capability_qa_documents_exist(self) -> None:
        for relative in ["docs/qa/capability-matrix.md", "docs/qa/skill-contract-tests.md", "docs/qa/behavior-acceptance-cases.json", "docs/qa/behavior-acceptance-report.json", "docs/qa/behavior-acceptance-status.json"]:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_capability_matrix_covers_all_creator_capabilities(self) -> None:
        text = (ROOT / "docs/qa/capability-matrix.md").read_text(encoding="utf-8")
        for capability in ["Routing", "Intake", "Execution Cycle", "Workspace State", "Rule Governance", "Skill Workbench", "Evidence Audit"]:
            self.assertIn(capability, text)

    def test_authoritative_skills_express_required_contracts(self) -> None:
        for skill, concepts in REQUIRED_CONCEPTS.items():
            text = (SKILL_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            for concept in concepts:
                with self.subTest(skill=skill, concept=concept):
                    self.assertIn(concept, text)

    def test_all_thirteen_project_types_have_three_reference_files(self) -> None:
        type_root = SKILL_ROOT / "creator-intake-planner/references/types"
        type_dirs = sorted(path for path in type_root.iterdir() if path.is_dir())
        self.assertEqual(len(type_dirs), 13)
        for type_dir in type_dirs:
            for filename in ["guide.md", "config.md", "skill-loadout.md"]:
                self.assertTrue((type_dir / filename).is_file())

    def test_plugin_mirror_matches_authoritative_skills(self) -> None:
        self.assertEqual(synchronize(SKILL_ROOT, PLUGIN_SKILL_ROOT, write=False), [])

    def test_exactly_seven_authoritative_skills_exist(self) -> None:
        found = sorted(path.name for path in SKILL_ROOT.iterdir() if (path / "SKILL.md").is_file())
        self.assertEqual(found, sorted(SKILLS))

    def test_plugin_uses_authoritative_version_and_identity(self) -> None:
        manifest = json.loads((ROOT / "plugin/creator-toolchain/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], read_version(ROOT))
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["author"]["name"], "crizleung21")
        self.assertEqual(manifest["interface"]["developerName"], "crizleung21")

    def test_readme_documents_install_and_validation_entrypoints(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in ["codex plugin marketplace add crizleung21/creator-toolchain", "codex plugin add creator-toolchain@creator-toolchain", "scripts/package_integrity.py", "scripts/build_plugin_package.py", "LICENSE"]:
            self.assertIn(required, text)

    def test_behavior_acceptance_catalog_has_34_cases(self) -> None:
        catalog = json.loads((ROOT / "docs/qa/behavior-acceptance-cases.json").read_text(encoding="utf-8"))
        cases = catalog["cases"]
        modes = [case["source_mode"] for case in cases]
        self.assertEqual(catalog["case_count"], 34)
        self.assertEqual(len(cases), 34)
        self.assertEqual(len({case["case_id"] for case in cases}), 34)
        self.assertEqual(modes.count("plugin-only"), 27)
        self.assertEqual(modes.count("repo-local"), 7)

    def test_behavior_evidence_is_current_or_explicitly_stale(self) -> None:
        report = json.loads((ROOT / "docs/qa/behavior-acceptance-report.json").read_text(encoding="utf-8"))
        status = json.loads((ROOT / "docs/qa/behavior-acceptance-status.json").read_text(encoding="utf-8"))
        package_report = json.loads((ROOT / "docs/qa/package-integrity-report.json").read_text(encoding="utf-8"))
        if status["status"] == "STALE":
            self.assertTrue(status["rerun_required"])
            self.assertEqual(status["current_package_payload_sha256"], package_report["payload_sha256"])
            self.assertNotEqual(report["package_payload_sha256"], package_report["payload_sha256"])
            return
        self.assertEqual(status["status"], "CURRENT")
        self.assertFalse(status["rerun_required"])
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["case_count"], 34)
        self.assertEqual(report["passed"], 34)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["errored"], 0)
        self.assertEqual(report["package_payload_sha256"], package_report["payload_sha256"])
        archive = ROOT / status["evidence_archive"]
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), status["evidence_archive_sha256"])
        with zipfile.ZipFile(archive) as evidence_zip:
            for case in report["cases"]:
                inner = case["raw_response_path"].split("!/", 1)[1]
                raw = evidence_zip.read(inner)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), case["raw_response_sha256"])


if __name__ == "__main__":
    unittest.main()
