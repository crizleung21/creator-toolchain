from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.creator_intake_artifacts import create_intake_package
from scripts.creator_planning_gate import evaluate_plan

ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = "2026-07-18T00:00:00Z"


def request(**overrides):
    value = {
        "title": "Creator Asset Naming Checker",
        "project_type": "utility",
        "goal": "Validate a directory manifest and report invalid or duplicate asset names.",
        "context": "Creators need deterministic asset naming before publishing.",
        "scope": ["Read a manifest", "Report duplicates", "Report invalid names"],
        "out_of_scope": ["Rename source files", "Upload assets"],
        "source_assets": [],
        "acceptance_criteria": [
            {"id": "AC-1", "title": "Duplicates", "given": "a manifest with duplicate names", "when": "the checker runs", "then": "both duplicate rows are reported"},
            {"id": "AC-2", "title": "Invalid names", "given": "a manifest with invalid names", "when": "the checker runs", "then": "each invalid name includes a rule ID"},
            {"id": "AC-3", "title": "Determinism", "given": "the same manifest", "when": "the checker runs twice", "then": "the reports are byte-identical"},
        ],
        "risks": ["Path traversal", "Ambiguous naming rules"],
        "blocking_questions": [],
        "non_blocking_questions": [],
    }
    value.update(overrides)
    return value


class CreatorPlanningGateTests(unittest.TestCase):
    def test_complete_plan_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = create_intake_package(root, request(), timestamp=TIMESTAMP, registry_root=ROOT)
            self.assertEqual(result["result"], "pass")
            self.assertEqual(result["valid_acceptance_criteria"], 3)

    def test_non_blocking_questions_preserve_pass_with_concerns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = create_intake_package(root, request(non_blocking_questions=["Should CSV export be included later?"]), timestamp=TIMESTAMP, registry_root=ROOT)
            self.assertEqual(result["result"], "pass_with_non_blocking_questions")

    def test_blocking_question_fails_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = create_intake_package(root, request(blocking_questions=["Which naming specification is authoritative?"]), timestamp=TIMESTAMP, registry_root=ROOT)
            self.assertEqual(result["result"], "fail_needs_more_planning")
            project = json.loads((Path(result["plan_dir"]) / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project["stage"], "ideating")

    def test_unresolved_source_asset_fails_unless_marked_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            failed = create_intake_package(root, request(title="Missing Source", source_assets=["fixtures/missing.json"]), timestamp=TIMESTAMP, registry_root=ROOT)
            self.assertEqual(failed["result"], "fail_needs_more_planning")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            passed = create_intake_package(root, request(title="Declared Missing Source", source_assets=["MISSING: naming specification pending"]), timestamp=TIMESTAMP, registry_root=ROOT)
            self.assertEqual(passed["result"], "pass")

    def test_unexpected_artifact_invalidates_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = create_intake_package(root, request(), timestamp=TIMESTAMP, registry_root=ROOT)
            plan_dir = Path(result["plan_dir"])
            (plan_dir / "implementation.py").write_text("pass\n", encoding="utf-8")
            report = evaluate_plan(plan_dir, workspace_root=root, evaluated_at=TIMESTAMP)
            self.assertEqual(report["result"], "fail_needs_more_planning")
            self.assertIn("GATE_ARTIFACT_UNEXPECTED", {item["check_id"] for item in report["findings"]})


if __name__ == "__main__":
    unittest.main()
