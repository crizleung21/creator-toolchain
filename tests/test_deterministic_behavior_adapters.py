from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.adapters.deterministic_contract_evaluator import evaluate_response
from scripts.adapters.deterministic_contract_response import generate_response
from scripts.evaluate_behavior_observations import evaluate_case

ROOT = Path(__file__).resolve().parents[1]


class DeterministicBehaviorAdapterTests(unittest.TestCase):
    def test_complete_catalog_passes_reference_conformance(self) -> None:
        catalog = json.loads((ROOT / "docs/qa/behavior-acceptance-cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["cases"]), 34)
        for case in catalog["cases"]:
            with self.subTest(case_id=case["case_id"]):
                response = generate_response({"case": case})
                evaluation = evaluate_response({
                    "case": case,
                    "selected_skill": response["selected_skill"],
                    "response_text": response["response_text"],
                })
                normalized = evaluate_case(case, response["response_text"], response["selected_skill"], evaluation)
                self.assertEqual(normalized["result"], "PASS")

    def test_response_is_hidden_rubric_blind(self) -> None:
        case = {
            "case_id": "ORCH-P01",
            "source_mode": "plugin-only",
            "prompt": "Route this idea.",
            "expected_skill": "creator-orchestrator",
            "required_observations": ["SECRET-RUBRIC-REQUIRED"],
            "prohibited_observations": ["SECRET-RUBRIC-PROHIBITED"],
        }
        response = generate_response({"case": case})["response_text"]
        self.assertNotIn("SECRET-RUBRIC-REQUIRED", response)
        self.assertNotIn("SECRET-RUBRIC-PROHIBITED", response)

    def test_evaluator_surfaces_a_prohibited_action_claim(self) -> None:
        case = {
            "case_id": "X",
            "expected_skill": "creator-orchestrator",
            "required_observations": ["route the idea to intake"],
            "prohibited_observations": ["edit product files"],
        }
        evaluation = evaluate_response({
            "case": case,
            "selected_skill": "creator-orchestrator",
            "response_text": "route the idea to intake\nedit product files",
        })
        self.assertEqual(evaluation["prohibited_observations"][0]["result"], "PRESENT")


if __name__ == "__main__":
    unittest.main()
