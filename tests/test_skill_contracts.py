from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from scripts.sync_plugin_skills import SKILLS, synchronize


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills"
PLUGIN_SKILL_ROOT = ROOT / "plugin/creator-toolchain/skills"


REQUIRED_CONCEPTS = {
    "creator-intake-planner": [
        "creator-intake:start",
        "INTAKE-STATE.md",
        "Planning Quality Gate",
        "scaffold",
        "handoff",
    ],
    "creator-execution-cycle": [
        "PLAN",
        "EXECUTE",
        "VERIFY",
        "RECONCILE",
        "DONE_WITH_CONCERNS",
        "activity_ledger.jsonl",
    ],
    "creator-workspace-manager": [
        ".creator/workspace.json",
        "creator-workspace:health-check",
        "creator-workspace:maintenance-review",
        "Session Insights",
    ],
    "creator-rule-router": [
        "GLOBAL",
        "stage-proposal",
        "recall",
        "exclude",
        "audit-conflicts",
    ],
    "creator-skill-workbench": [
        "discover",
        "scaffold",
        "distill",
        "score",
        "audit",
    ],
    "creator-evidence-audit": [
        "Phase 0",
        "Phase 8",
        "Findings",
        "Remediation Guidance",
        "Execution Handoff",
        "does not directly mutate",
    ],
}


class SkillContractTests(unittest.TestCase):
    def test_capability_qa_documents_exist(self) -> None:
        self.assertTrue((ROOT / "docs/qa/capability-matrix.md").is_file())
        self.assertTrue((ROOT / "docs/qa/skill-contract-tests.md").is_file())
        self.assertTrue((ROOT / "docs/qa/behavior-acceptance-cases.json").is_file())
        self.assertTrue((ROOT / "docs/qa/behavior-acceptance-report.json").is_file())

    def test_capability_matrix_covers_all_creator_capabilities(self) -> None:
        text = (ROOT / "docs/qa/capability-matrix.md").read_text(encoding="utf-8")
        for capability in [
            "Routing",
            "Intake",
            "Execution Cycle",
            "Workspace State",
            "Rule Governance",
            "Skill Workbench",
            "Evidence Audit",
        ]:
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
        self.assertTrue(type_root.is_dir())
        type_dirs = sorted(path for path in type_root.iterdir() if path.is_dir())
        self.assertEqual(len(type_dirs), 13)
        for type_dir in type_dirs:
            for filename in ["guide.md", "config.md", "skill-loadout.md"]:
                with self.subTest(type_id=type_dir.name, filename=filename):
                    self.assertTrue((type_dir / filename).is_file())

    def test_plugin_mirror_matches_authoritative_skills(self) -> None:
        self.assertEqual(
            synchronize(SKILL_ROOT, PLUGIN_SKILL_ROOT, write=False),
            [],
        )

    def test_exactly_seven_authoritative_skills_exist(self) -> None:
        found = sorted(path.name for path in SKILL_ROOT.iterdir() if (path / "SKILL.md").is_file())
        self.assertEqual(found, sorted(SKILLS))

    def test_plugin_uses_stable_version_and_identity(self) -> None:
        manifest_path = ROOT / "plugin/creator-toolchain/.codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "1.0.1")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["author"]["name"], "crizleung21")
        self.assertEqual(manifest["interface"]["developerName"], "crizleung21")

    def test_readme_documents_current_install_and_validation(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in [
            "codex plugin marketplace add crizleung21/creator-toolchain --ref v1.0.1 --json",
            "codex plugin add creator-toolchain@creator-toolchain --json",
            "scripts/package_integrity.py",
            "scripts/build_plugin_package.py",
            "LICENSE",
        ]:
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_behavior_acceptance_catalog_has_34_cases(self) -> None:
        catalog_path = ROOT / "docs/qa/behavior-acceptance-cases.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        cases = catalog["cases"]
        ids = [case["case_id"] for case in cases]
        modes = [case["source_mode"] for case in cases]

        self.assertEqual(catalog["case_count"], 34)
        self.assertEqual(len(cases), 34)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("ORCH-P01", ids)
        self.assertIn("ORCH-N01", ids)
        self.assertEqual(modes.count("plugin-only"), 27)
        self.assertEqual(modes.count("repo-local"), 7)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                self.assertTrue(case["expected_skill"])
                self.assertTrue(case["required_observations"])
                self.assertTrue(case["prohibited_observations"])

    def test_behavior_acceptance_report_has_34_verified_artifacts(self) -> None:
        report_path = ROOT / "docs/qa/behavior-acceptance-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        catalog = json.loads(
            (ROOT / "docs/qa/behavior-acceptance-cases.json").read_text(encoding="utf-8")
        )
        catalog_by_id = {case["case_id"]: case for case in catalog["cases"]}
        package_report = json.loads(
            (ROOT / "docs/qa/package-integrity-report.json").read_text(encoding="utf-8")
        )

        self.assertEqual(report["schema_version"], "1.0.0")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["case_count"], 34)
        self.assertEqual(report["passed"], 34)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(
            report["package_payload_sha256"], package_report["payload_sha256"]
        )
        self.assertEqual(len(report["cases"]), 34)
        report_ids = {case["case_id"] for case in report["cases"]}
        self.assertEqual(report_ids, set(catalog_by_id))
        for case in report["cases"]:
            with self.subTest(case_id=case["case_id"]):
                expected = catalog_by_id[case["case_id"]]
                self.assertEqual(case["source_mode"], expected["source_mode"])
                self.assertEqual(case["selected_skill"], expected["expected_skill"])
                self.assertEqual(case["codex_version"], "0.142.3")
                self.assertEqual(case["execution_mode"], "ephemeral-read-only")
                self.assertEqual(case["result"], "PASS")
                required_reviews = case["required_observations"]
                prohibited_reviews = case["prohibited_observations"]
                self.assertEqual(
                    {item["observation"] for item in required_reviews},
                    set(expected["required_observations"]),
                )
                self.assertEqual(
                    {item["observation"] for item in prohibited_reviews},
                    set(expected["prohibited_observations"]),
                )
                self.assertTrue(all(item["result"] == "PASS" for item in required_reviews))
                self.assertTrue(all(item["result"] == "ABSENT" for item in prohibited_reviews))
                self.assertEqual(
                    case["artifact_path"],
                    f"docs/qa/behavior-acceptance/{case['case_id']}.md",
                )
                artifact = ROOT / case["artifact_path"]
                self.assertTrue(artifact.is_file())
                self.assertEqual(
                    hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    case["artifact_sha256"],
                )


if __name__ == "__main__":
    unittest.main()
