from __future__ import annotations

import hashlib
import json
import unittest
import zipfile
from pathlib import Path

from scripts.sync_plugin_skills import SKILLS, synchronize


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
            with self.subTest(capability=capability):
                self.assertIn(capability, text)

    def test_authoritative_skills_express_required_contracts(self) -> None:
        for skill, concepts in REQUIRED_CONCEPTS.items():
            skill_file = SKILL_ROOT / skill / "SKILL.md"
            self.assertTrue(skill_file.is_file(), skill)
            text = skill_file.read_text(encoding="utf-8")
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

    def test_plugin_uses_stable_version_and_identity(self) -> None:
        manifest = json.loads((ROOT / "plugin/creator-toolchain/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "1.0.1")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["author"]["name"], "crizleung21")
        self.assertEqual(manifest["interface"]["developerName"], "crizleung21")

    def test_readme_documents_current_install_and_validation(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in ["codex plugin marketplace add crizleung21/creator-toolchain --ref v1.0.1 --json", "codex plugin add creator-toolchain@creator-toolchain --json", "scripts/package_integrity.py", "scripts/build_plugin_package.py", "LICENSE"]:
            self.assertIn(required, text)

    def test_behavior_acceptance_catalog_has_34_cases(self) -> None:
        catalog = json.loads((ROOT / "docs/qa/behavior-acceptance-cases.json").read_text(encoding="utf-8"))
        cases = catalog["cases"]
        ids = [case["case_id"] for case in cases]
        modes = [case["source_mode"] for case in cases]
        self.assertEqual(catalog["case_count"], 34)
        self.assertEqual(len(cases), 34)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(modes.count("plugin-only"), 27)
        self.assertEqual(modes.count("repo-local"), 7)

    def test_behavior_acceptance_report_has_current_evidence_archive(self) -> None:
        report = json.loads((ROOT / "docs/qa/behavior-acceptance-report.json").read_text(encoding="utf-8"))
        status = json.loads((ROOT / "docs/qa/behavior-acceptance-status.json").read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / "docs/qa/behavior-acceptance-cases.json").read_text(encoding="utf-8"))
        package_report = json.loads((ROOT / "docs/qa/package-integrity-report.json").read_text(encoding="utf-8"))
        catalog_by_id = {case["case_id"]: case for case in catalog["cases"]}

        self.assertEqual(report["schema_version"], "1.0.0")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["case_count"], 34)
        self.assertEqual(report["passed"], 34)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["errored"], 0)
        self.assertTrue(report["all_catalog_cases_run"])
        self.assertEqual(report["package_payload_sha256"], package_report["payload_sha256"])
        self.assertEqual(status["status"], "CURRENT")
        self.assertFalse(status["rerun_required"])
        self.assertEqual(status["report_commit_sha"], report["commit_sha"])

        archive = ROOT / status["evidence_archive"]
        self.assertTrue(archive.is_file())
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), status["evidence_archive_sha256"])
        self.assertEqual({case["case_id"] for case in report["cases"]}, set(catalog_by_id))
        with zipfile.ZipFile(archive) as evidence_zip:
            for case in report["cases"]:
                expected = catalog_by_id[case["case_id"]]
                self.assertEqual(case["source_mode"], expected["source_mode"])
                self.assertEqual(case["selected_skill"], expected["expected_skill"])
                self.assertTrue(case["codex_version"].startswith("creator-contract-runtime/"))
                self.assertEqual(case["model_version"], "deterministic-provider-neutral-reference")
                self.assertEqual(case["result"], "PASS")
                inner_path = case["raw_response_path"].split("!/", 1)[1]
                raw = evidence_zip.read(inner_path)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), case["raw_response_sha256"])
                lines = raw.decode("utf-8").splitlines()
                for item in case["required_observations"]:
                    self.assertEqual(item["result"], "PASS")
                    excerpt = "\n".join(lines[item["response_line_start"] - 1:item["response_line_end"]]).strip()
                    self.assertEqual(excerpt, item["evidence_excerpt"])
                for item in case["prohibited_observations"]:
                    self.assertEqual(item["result"], "ABSENT")
                    self.assertIsNone(item["response_line_start"])
                    self.assertIsNone(item["response_line_end"])


if __name__ == "__main__":
    unittest.main()
