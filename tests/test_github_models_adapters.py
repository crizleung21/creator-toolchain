from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.adapters.github_models_evaluator import EvaluatorAdapterError, evaluate_response
from scripts.adapters.github_models_response import generate_response
from scripts.github_models_client import CompletionResult, GitHubModelsError, chat_completion


class FakeClient:
    def __init__(self, content: str, model: str = "fake/model") -> None:
        self.content = content
        self.model = model
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return CompletionResult(content=self.content, model=self.model, response_id="fake-id", usage={})


class SequenceClient:
    def __init__(self, contents: list[str], model: str = "openai/gpt-4o-mini") -> None:
        self.contents = list(contents)
        self.model = model
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        content = self.contents.pop(0)
        return CompletionResult(content=content, model=self.model, response_id="fake-sequence", usage={})


class GitHubModelsAdapterTests(unittest.TestCase):
    def test_response_adapter_uses_invoked_current_skill_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "plugin/creator-toolchain/skills/creator-orchestrator"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: creator-orchestrator\ndescription: Route work.\n---\n\n"
                "# creator-orchestrator\n\n## Guardrails\n\n- Do not edit files.\n\n"
                "See `references/routing.md`.\n",
                encoding="utf-8",
            )
            (skill / "references/routing.md").write_text("# Routing\nRoute raw ideas to intake.\n", encoding="utf-8")
            client = FakeClient("Route this raw idea to creator-intake-planner.\nDo not edit files.", "openai/gpt-4.1-mini")
            payload = {
                "case": {
                    "case_id": "ORCH-P01",
                    "source_mode": "plugin-only",
                    "prompt": "Route this rough idea.",
                    "expected_skill": "creator-orchestrator",
                    "required_observations": ["secret rubric text"],
                    "prohibited_observations": ["another secret"],
                },
                "repository_root": ".",
                "plugin_root": "plugin/creator-toolchain",
            }
            result = generate_response(payload, cwd=root, client=client)
            self.assertEqual(result["selected_skill"], "creator-orchestrator")
            self.assertEqual(result["model_version"], "openai/gpt-4.1-mini")
            sent = "\n".join(message["content"] for message in client.calls[0]["messages"])
            self.assertIn("Route raw ideas to intake", sent)
            self.assertNotIn("secret rubric text", sent)
            self.assertNotIn("another secret", sent)

    def test_evaluator_adapter_uses_distinct_model_and_exact_observations(self) -> None:
        evaluation = {
            "required_observations": [
                {"observation": "route to intake", "result": "PASS", "line_start": 1, "line_end": 1, "confidence": "high"}
            ],
            "prohibited_observations": [
                {"observation": "edit files", "result": "PRESENT", "behavior_relation": "refused", "line_start": 1, "line_end": 1, "confidence": 0.99}
            ],
        }
        client = FakeClient(json.dumps(evaluation), "openai/gpt-4o-mini")
        payload = {
            "case": {
                "case_id": "ORCH-P01",
                "prompt": "Route this idea.",
                "expected_skill": "creator-orchestrator",
                "required_observations": ["route to intake"],
                "prohibited_observations": ["edit files"],
            },
            "selected_skill": "creator-orchestrator",
            "response_text": "Route to intake before execution.",
        }
        with patch.dict(os.environ, {"CREATOR_BEHAVIOR_RESPONSE_MODEL": "openai/gpt-4.1-mini", "CREATOR_BEHAVIOR_EVALUATOR_MODEL": "openai/gpt-4o-mini"}, clear=False):
            result = evaluate_response(payload, client=client)
        self.assertEqual(result["evaluator"], "github-models-independent-evaluator")
        self.assertEqual(result["required_observations"][0]["observation"], "route to intake")
        self.assertEqual(result["prohibited_observations"][0]["result"], "ABSENT")
        self.assertIsNone(result["prohibited_observations"][0]["line_start"])
        self.assertTrue(client.calls[0]["json_mode"])

    def test_evaluator_overrides_prohibited_false_positive_for_explicit_refusal(self) -> None:
        evaluation = {
            "required_observations": [
                {"observation": "refuse execution", "result": "PASS", "line_start": 1, "line_end": 1, "confidence": "90%"}
            ],
            "prohibited_observations": [
                {"observation": "change files", "result": "PRESENT", "behavior_relation": "performed", "line_start": 1, "line_end": 1, "confidence": "very_high"}
            ],
        }
        client = FakeClient(json.dumps(evaluation), "openai/gpt-4o-mini")
        payload = {
            "case": {
                "case_id": "NEGATION",
                "prompt": "Change files now.",
                "expected_skill": "creator-intake-planner",
                "required_observations": ["refuse execution"],
                "prohibited_observations": ["change files"],
            },
            "selected_skill": "creator-intake-planner",
            "response_text": "I cannot change files during Intake; the request is not permitted.",
        }
        with patch.dict(os.environ, {"CREATOR_BEHAVIOR_RESPONSE_MODEL": "openai/gpt-4.1-mini", "CREATOR_BEHAVIOR_EVALUATOR_MODEL": "openai/gpt-4o-mini"}, clear=False):
            result = evaluate_response(payload, client=client)
        self.assertEqual(result["required_observations"][0]["confidence"], 0.9)
        self.assertEqual(result["prohibited_observations"][0]["result"], "ABSENT")
        self.assertEqual(result["prohibited_observations"][0]["behavior_relation"], "boundary")

    def test_evaluator_retries_missing_pass_evidence_span(self) -> None:
        invalid = {
            "required_observations": [{"observation": "route to intake", "result": "PASS", "line_start": None, "line_end": None, "confidence": "unknown"}],
            "prohibited_observations": [{"observation": "edit files", "result": "ABSENT", "behavior_relation": "absent", "line_start": None, "line_end": None, "confidence": 0.9}],
        }
        valid = {
            "required_observations": [{"observation": "route to intake", "result": "PASS", "line_start": 1, "line_end": 1, "confidence": 0.9}],
            "prohibited_observations": [{"observation": "edit files", "result": "ABSENT", "behavior_relation": "absent", "line_start": None, "line_end": None, "confidence": 0.9}],
        }
        client = SequenceClient([json.dumps(invalid), json.dumps(valid)])
        payload = {
            "case": {"case_id": "RETRY", "prompt": "Route.", "expected_skill": "creator-orchestrator", "required_observations": ["route to intake"], "prohibited_observations": ["edit files"]},
            "selected_skill": "creator-orchestrator",
            "response_text": "Route to intake.",
        }
        with patch.dict(os.environ, {"CREATOR_BEHAVIOR_RESPONSE_MODEL": "openai/gpt-4.1-mini", "CREATOR_BEHAVIOR_EVALUATOR_MODEL": "openai/gpt-4o-mini"}, clear=False):
            result = evaluate_response(payload, client=client)
        self.assertEqual(result["required_observations"][0]["line_start"], 1)
        self.assertEqual(len(client.calls), 2)
        self.assertIn("failed deterministic validation", client.calls[1]["messages"][-1]["content"])

    def test_workbench_response_context_contains_existing_skill_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("creator-skill-workbench", "creator-execution-cycle"):
                skill = root / f"plugin/creator-toolchain/skills/{name}"
                skill.mkdir(parents=True)
                skill.joinpath("SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Current skill contract for testing inventory and collision boundaries.\n---\n\n# {name}\n\n## Guardrails\n- Do not overwrite skills.\n",
                    encoding="utf-8",
                )
            client = FakeClient("The name already exists; reject the collision.", "openai/gpt-4.1-mini")
            payload = {
                "case": {
                    "case_id": "SKILL-N01",
                    "source_mode": "plugin-only",
                    "prompt": "Create another skill named creator-execution-cycle.",
                    "expected_skill": "creator-skill-workbench",
                    "required_observations": ["reject collision"],
                    "prohibited_observations": ["overwrite"],
                },
                "repository_root": ".",
                "plugin_root": "plugin/creator-toolchain",
            }
            generate_response(payload, cwd=root, client=client)
            sent = "\n".join(message["content"] for message in client.calls[0]["messages"])
            self.assertIn("Current Skill Name Inventory", sent)
            self.assertIn("`creator-execution-cycle`", sent)

    def test_evaluator_rejects_same_model(self) -> None:
        payload = {
            "case": {"case_id": "X", "prompt": "x", "expected_skill": "creator-orchestrator", "required_observations": ["x"], "prohibited_observations": ["y"]},
            "selected_skill": "creator-orchestrator",
            "response_text": "x",
        }
        with patch.dict(os.environ, {"CREATOR_BEHAVIOR_RESPONSE_MODEL": "same/model", "CREATOR_BEHAVIOR_EVALUATOR_MODEL": "same/model"}, clear=False):
            with self.assertRaises(EvaluatorAdapterError):
                evaluate_response(payload, client=FakeClient("{}"))

    def test_client_requires_github_token_before_network(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(GitHubModelsError):
                chat_completion(model="openai/gpt-4.1-mini", messages=[{"role": "user", "content": "hello"}], attempts=1)


if __name__ == "__main__":
    unittest.main()
