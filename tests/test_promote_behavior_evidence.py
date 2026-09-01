from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.promote_behavior_evidence import PromotionError, promote


COMMIT = "a" * 40
PAYLOAD = "b" * 64


class PromoteBehaviorEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        (self.root / "docs/qa").mkdir(parents=True)
        (self.root / "docs/implementation/phase-7").mkdir(parents=True)
        (self.root / "docs/qa/package-integrity-report.json").write_text(
            json.dumps({"payload_sha256": PAYLOAD}) + "\n",
            encoding="utf-8",
        )
        self.evidence_root = self.root / ".phase9/behavior"
        response_root = self.evidence_root / "responses"
        response_root.mkdir(parents=True)
        cases = []
        for index in range(34):
            case_id = f"CASE-{index:02d}"
            raw_relative = f".phase9/behavior/responses/{case_id}.txt"
            (self.root / raw_relative).write_text(
                f"response {index}\n", encoding="utf-8"
            )
            cases.append(
                {
                    "case_id": case_id,
                    "raw_response_path": raw_relative,
                    "result": "PASS",
                }
            )
        self.report = {
            "schema_version": "1.0.0",
            "status": "PASS",
            "run_id": "phase9-test",
            "case_count": 34,
            "passed": 34,
            "failed": 0,
            "errored": 0,
            "all_catalog_cases_run": True,
            "commit_sha": COMMIT,
            "package_payload_sha256": PAYLOAD,
            "catalog_sha256": "c" * 64,
            "harness_version": "1.0.0",
            "runtime_adapter": "fixture-response",
            "evaluator_adapter": "fixture-evaluator",
            "cases": cases,
        }
        self.report_path = self.evidence_root / "report.json"
        self.report_path.write_text(
            json.dumps(self.report, indent=2) + "\n", encoding="utf-8"
        )

    def test_repository_relative_run_is_promoted_under_archive_root(self) -> None:
        status = promote(
            self.root,
            report_path=self.report_path,
            evidence_root=self.evidence_root,
            tested_commit=COMMIT,
            promotion_run_id=123,
            recorded_at="2026-09-01T00:00:00Z",
        )

        self.assertEqual(status["status"], "CURRENT")
        canonical = json.loads(
            (self.root / "docs/qa/behavior-acceptance-report.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            canonical["cases"][0]["raw_response_path"],
            "docs/qa/behavior-acceptance-current.zip!/responses/CASE-00.txt",
        )
        archive_path = self.root / "docs/qa/behavior-acceptance-current.zip"
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(archive.read("responses/CASE-00.txt"), b"response 0\n")

    def test_raw_response_outside_declared_evidence_root_is_rejected(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_text("unsafe\n", encoding="utf-8")
        self.report["cases"][0]["raw_response_path"] = "outside.txt"
        self.report_path.write_text(
            json.dumps(self.report, indent=2) + "\n", encoding="utf-8"
        )

        with self.assertRaises(PromotionError):
            promote(
                self.root,
                report_path=self.report_path,
                evidence_root=self.evidence_root,
                tested_commit=COMMIT,
                promotion_run_id=123,
                recorded_at="2026-09-01T00:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
