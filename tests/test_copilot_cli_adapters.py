from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.adapters.copilot_cli_evaluator import EvaluatorAdapterError, evaluate_response
from scripts.adapters.copilot_cli_response import generate_response
from scripts.copilot_cli_client import CopilotCLIError, CopilotResult, run_copilot
from scripts.probe_copilot_models import ModelProbeError, select_available_models


class FakeCopilotClient:
    def __init__(self, content: str, model: str = "gpt-5.4", cli_version: str = "1.0.0") -> None:
        self.result = CopilotResult(content=content, model=model, cli_version=cli_version)
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class FakeRunner:
    def __init__(self) -> None:
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if argv[1:] == ["version"]:
            return subprocess.CompletedProcess(argv, 0, stdout="GitHub Copilot CLI 1.2.3\n", stderr="")
        return subprocess.CompletedProcess(argv, 0, stdout="Read-only response.\n", stderr="")


class ProbeClient:
    def __init__(self, available: set[str]) -> None:
        self.available = available
        self.calls: list[str] = []

    def __call__(self, *, prompt: str, model: str, timeout: int) -> CopilotResult:
        self.calls.append(model)
        if model not in self.available:
            raise CopilotCLIError(f"model unavailable: {model}")
        return CopilotResult(content="OK", model=model, cli_version="1.2.3")


class CopilotCLIAdapterTests(unittest.TestCase):
    def test_client_requires_token_before_execution(self) -> None:
        with self.assertRaises(CopilotCLIError):
            run_copilot(prompt="hello", model="gpt-5.4", environment={"PATH": "/bin"})

    def test_client_uses_locked_down_programmatic_flags(self) -> None:
        runner = FakeRunner()
        result = run_copilot(
            prompt="Return a read-only answer.",
            model="gpt-5.4",
            environment={"GITHUB_TOKEN": "token", "PATH": "/usr/bin"},
            runner=runner,
        )
        argv = runner.calls[0][0]
        self.assertEqual(result.content, "Read-only response.")
        self.assertIn("--no-custom-instructions", argv)
        self.assertIn("--disable-builtin-mcps", argv)
        self.assertIn("--no-ask-user", argv)
        self.assertIn("--deny-tool=shell,write,read,url,memory", argv)
        self.assertIn("--model=gpt-5.4", argv)
        self.assertNotIn("--yolo", argv)
        self.assertNotIn("--no-banner", argv)

    def test_model_probe_selects_first_two_distinct_successes(self) -> None:
        client = ProbeClient({"model-b", "model-d"})
        report = select_available_models(
            ["model-a", "model-b", "model-b", "model-c", "model-d", "model-e"],
            client=client,
        )
        self.assertEqual(report["response_model"], "model-b")
        self.assertEqual(report["evaluator_model"], "model-d")
        self.assertTrue(report["distinct_models"])
        self.assertEqual(client.calls, ["model-a", "model-b", "model-c", "model-d"])

    def test_model_probe_fails_when_only_one_model_is_available(self) -> None:
        client = ProbeClient({"model-b"})
        with self.assertRaises(ModelProbeError):
            select_available_models(["model-a", "model-b", "model-c"], client=client)

    def test_response_adapter_is_rubric_blind_and_adds_intake_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "plugin/creator-toolchain/skills/creator-intake-planner"
            skill.mkdir(parents=True)
            skill.joinpath("SKILL.md").write_text(
                "---\nname: creator-intake-planner\ndescription: Resume typed Intake safely.\n---\n"
                "# creator-intake-planner\n\n## Guardrails\nDo not scaffold a failed gate.\n",
                encoding="utf-8",
            )
            client = FakeCopilotClient("The checkpoint lacks acceptance criteria, so Scaffold is blocked.")
            payload = {
                "case": {
                    "case_id": "INTAKE-P02",
                    "source_mode": "plugin-only",
                    "prompt": "Resume this checkpoint from INTAKE-STATE.md.",
                    "expected_skill": "creator-intake-planner",
                    "required_observations": ["secret rubric text"],
                    "prohibited_observations": ["another secret"],
                },
                "repository_root": ".",
                "plugin_root": "plugin/creator-toolchain",
            }
            result = generate_response(payload, cwd=root, client=client)
            sent = client.calls[0]["prompt"]
            self.assertNotIn("secret rubric text", sent)
            self.assertNotIn("another secret", sent)
            self.assertIn("### Blocking Questions", result["response_text"])
            self.assertIn("### Non-Blocking Questions", result["response_text"])
            self.assertIn("fail_needs_more_planning", result["response_text"])

    def test_evaluator_uses_distinct_model_and_exact_observations(self) -> None:
        evaluation = {
            "required_observations": [
                {
                    "observation": "route to intake",
                    "result": "PASS",
                    "line_start": 1,
                    "line_end": 1,
                    "confidence": 0.9,
                }
            ],
            "prohibited_observations": [
                {
                    "observation": "edit files",
                    "result": "PRESENT",
                    "behavior_relation": "refused",
                    "line_start": 1,
                    "line_end": 1,
                    "confidence": 0.9,
                }
            ],
        }
        client = FakeCopilotClient(
            json.dumps(evaluation), model="claude-haiku-4.5", cli_version="1.2.3"
        )
        payload = {
            "case": {
                "case_id": "ORCH-P01",
                "prompt": "Route.",
                "expected_skill": "creator-orchestrator",
                "required_observations": ["route to intake"],
                "prohibited_observations": ["edit files"],
            },
            "selected_skill": "creator-orchestrator",
            "response_text": "Route to intake; do not edit files.",
        }
        with patch.dict(
            os.environ,
            {
                "CREATOR_BEHAVIOR_RESPONSE_MODEL": "gpt-5.4",
                "CREATOR_BEHAVIOR_EVALUATOR_MODEL": "claude-haiku-4.5",
            },
            clear=False,
        ):
            result = evaluate_response(payload, client=client)
        self.assertEqual(result["required_observations"][0]["observation"], "route to intake")
        self.assertEqual(result["prohibited_observations"][0]["result"], "ABSENT")
        self.assertIsNone(result["prohibited_observations"][0]["line_start"])
        self.assertIn("github-copilot-cli-independent-evaluator", result["evaluator"])

    def test_evaluator_rejects_same_model(self) -> None:
        payload = {
            "case": {
                "case_id": "X",
                "prompt": "x",
                "expected_skill": "creator-orchestrator",
                "required_observations": ["x"],
                "prohibited_observations": ["y"],
            },
            "selected_skill": "creator-orchestrator",
            "response_text": "x",
        }
        with patch.dict(
            os.environ,
            {
                "CREATOR_BEHAVIOR_RESPONSE_MODEL": "same-model",
                "CREATOR_BEHAVIOR_EVALUATOR_MODEL": "same-model",
            },
            clear=False,
        ):
            with self.assertRaises(EvaluatorAdapterError):
                evaluate_response(payload, client=FakeCopilotClient("{}"))


if __name__ == "__main__":
    unittest.main()
