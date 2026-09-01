from __future__ import annotations

import itertools
import json
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.evaluate_behavior_observations import ObservationEvaluationError, evaluate_case
from scripts.run_behavior_acceptance import HARNESS_VERSION, BehaviorAcceptanceError, assess_report_freshness, run_behavior_acceptance, validate_catalog

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "a" * 40
PAYLOAD = "b" * 64


def timestamps():
    counter = itertools.count()
    def next_timestamp() -> str:
        value = next(counter)
        return f"2026-07-23T13:{value:02d}:00Z"
    return next_timestamp


class BehaviorAcceptanceRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        (self.root / "docs/qa").mkdir(parents=True)
        self.catalog = {"schema_version": "1.0.0", "case_count": 2, "cases": [{"case_id": "CASE-P01", "source_mode": "plugin-only", "prompt": "Route the request.", "expected_skill": "creator-orchestrator", "required_observations": ["name one primary workflow", "preserve a planning boundary"], "prohibited_observations": ["mutate state"]}, {"case_id": "CASE-P02", "source_mode": "repo-local", "prompt": "Plan the idea.", "expected_skill": "creator-intake-planner", "required_observations": ["route to typed intake"], "prohibited_observations": ["edit product files"]}]}
        (self.root / "docs/qa/behavior-acceptance-cases.json").write_text(json.dumps(self.catalog, indent=2) + "\n", encoding="utf-8")
        (self.root / "docs/qa/package-integrity-report.json").write_text(json.dumps({"payload_sha256": PAYLOAD}) + "\n", encoding="utf-8")
        self.response_script = self.root / "fake_response.py"
        self.response_script.write_text('import json, sys\npayload=json.load(sys.stdin)\ncase=payload["case"]\nprint(json.dumps({"selected_skill":case["expected_skill"],"response_text":"\\n".join(case["required_observations"]),"codex_version":"test-codex","model_version":"test-model"}))\n', encoding="utf-8")
        self.evaluator_script = self.root / "fake_evaluator.py"
        self.evaluator_script.write_text('import json, sys\npayload=json.load(sys.stdin)\ncase=payload["case"]\nrequired=[{"observation":observation,"result":"PASS","line_start":index,"line_end":index,"confidence":1.0} for index,observation in enumerate(case["required_observations"],start=1)]\nprohibited=[{"observation":observation,"result":"ABSENT","line_start":None,"line_end":None,"confidence":1.0} for observation in case["prohibited_observations"]]\nprint(json.dumps({"evaluator":"fixture-evaluator","evaluator_version":"1.0.0","required_observations":required,"prohibited_observations":prohibited}))\n', encoding="utf-8")

    def command(self, path: Path) -> str:
        return f"{sys.executable} {path}"

    def test_catalog_validation_and_full_run_are_evidence_bound(self) -> None:
        self.assertEqual(len(validate_catalog(self.catalog)), 2)
        report = run_behavior_acceptance(self.root, response_command=self.command(self.response_script), evaluator_command=self.command(self.evaluator_script), run_id="fixture-pass", commit_sha=COMMIT, timestamp_factory=timestamps(), schema_root=ROOT)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["all_catalog_cases_run"])
        self.assertEqual(report["passed"], 2)
        first = report["cases"][0]
        self.assertEqual(first["required_observations"][0]["evidence_excerpt"], "name one primary workflow")
        self.assertEqual(first["required_observations"][0]["response_line_start"], 1)
        self.assertEqual(first["prohibited_observations"][0]["result"], "ABSENT")
        self.assertTrue((self.root / first["raw_response_path"]).is_file())
        freshness = assess_report_freshness(report, commit_sha=COMMIT, package_payload_sha256=PAYLOAD, catalog_sha256=report["catalog_sha256"])
        self.assertEqual(freshness["status"], "CURRENT")

    def test_partial_run_is_incomplete_and_cannot_satisfy_release_gate(self) -> None:
        report = run_behavior_acceptance(self.root, response_command=self.command(self.response_script), evaluator_command=self.command(self.evaluator_script), run_id="fixture-partial", commit_sha=COMMIT, case_ids=["CASE-P01"], timestamp_factory=timestamps(), schema_root=ROOT)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertFalse(report["all_catalog_cases_run"])
        self.assertEqual(report["case_count"], 1)

    def test_selected_skill_mismatch_forces_failure(self) -> None:
        wrong = self.root / "wrong_response.py"
        wrong.write_text('import json, sys\npayload=json.load(sys.stdin)\ncase=payload["case"]\nprint(json.dumps({"selected_skill":"creator-rule-router","response_text":"\\n".join(case["required_observations"]),"codex_version":"test-codex","model_version":"test-model"}))\n', encoding="utf-8")
        report = run_behavior_acceptance(self.root, response_command=self.command(wrong), evaluator_command=self.command(self.evaluator_script), run_id="fixture-fail", commit_sha=COMMIT, timestamp_factory=timestamps(), schema_root=ROOT)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["failed"], 2)

    def test_evaluator_rejects_unbound_or_out_of_range_evidence(self) -> None:
        case = self.catalog["cases"][0]
        evaluation = {"evaluator": "bad", "evaluator_version": "1", "required_observations": [{"observation": case["required_observations"][0], "result": "PASS", "line_start": 99, "line_end": 99, "confidence": 1.0}, {"observation": case["required_observations"][1], "result": "FAIL", "line_start": None, "line_end": None, "confidence": 0.5}], "prohibited_observations": [{"observation": case["prohibited_observations"][0], "result": "ABSENT", "line_start": None, "line_end": None, "confidence": 1.0}]}
        with self.assertRaises(ObservationEvaluationError):
            evaluate_case(case, "only one response line", case["expected_skill"], evaluation)

    def test_freshness_detects_commit_package_catalog_and_harness_changes(self) -> None:
        report = {"commit_sha": COMMIT, "package_payload_sha256": PAYLOAD, "catalog_sha256": "c" * 64, "harness_version": HARNESS_VERSION}
        result = assess_report_freshness(report, commit_sha="d" * 40, package_payload_sha256="e" * 64, catalog_sha256="f" * 64, harness_version="2.0.0")
        self.assertEqual(result["status"], "STALE")
        self.assertEqual({item["field"] for item in result["mismatches"]}, {"commit_sha", "package_payload_sha256", "catalog_sha256", "harness_version"})

    def test_existing_run_directory_is_never_overwritten(self) -> None:
        kwargs = dict(root=self.root, response_command=self.command(self.response_script), evaluator_command=self.command(self.evaluator_script), run_id="no-overwrite", commit_sha=COMMIT, timestamp_factory=timestamps(), schema_root=ROOT)
        run_behavior_acceptance(**kwargs)
        with self.assertRaises(BehaviorAcceptanceError):
            run_behavior_acceptance(**kwargs)


if __name__ == "__main__":
    unittest.main()
