from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.adapters.copilot_cli_evaluator import evaluate_response
from scripts.adapters.copilot_cli_response import generate_response
from scripts.copilot_cli_client import CopilotCLIError, CopilotResult, run_copilot
from scripts.probe_copilot_models import ModelProbeError, select_available_profiles


class FakeCopilotClient:
    def __init__(
        self,
        content: str,
        model: str = "auto",
        cli_version: str = "1.0.0",
        agent: str | None = None,
    ) -> None:
        self.result = CopilotResult(content=content, model=model, cli_version=cli_version, agent=agent)
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


class SessionClient:
    def __init__(self, fail_call: int | None = None) -> None:
        self.fail_call = fail_call
        self.calls: list[tuple[str, str | None]] = []

    def __call__(self, *, prompt: str, model: str, agent: str | None, timeout: int) -> CopilotResult:
        self.calls.append((model, agent))
        if self.fail_call == len(self.calls):
            raise CopilotCLIError("isolated session unavailable")
        return CopilotResult(content="OK", model=model, cli_version="1.2.3", agent=agent)


class CopilotCLIAdapterTests(unittest.TestCase):
    def test_client_requires_token_before_execution(self) -> None:
        with self.assertRaises(CopilotCLIError):
            run_copilot(prompt="hello", model="auto", environment={"PATH": "/bin"})

    def test_client_uses_locked_down_programmatic_flags(self) -> None:
        runner = FakeRunner()
        result = run_copilot(
            prompt="Return a read-only answer.",
            model="auto",
            environment={"GITHUB_TOKEN": "token", "PATH": "/usr/bin"},
            runner=runner,
        )
        argv = runner.calls[0][0]
        self.assertEqual(result.content, "Read-only response.")
        self.assertIn("--no-custom-instructions", argv)
        self.assertIn("--disable-builtin-mcps", argv)
        self.assertIn("--no-ask-user", argv)
        self.assertIn("--deny-tool=shell,write,read,url,memory", argv)
        self.assertIn("--model=auto", argv)
        self.assertNotIn("--yolo", argv)
        self.assertNotIn("--no-banner", argv)

    def test_client_can_select_an_agent_when_platform_supports_it(self) -> None:
        runner = FakeRunner()
        result = run_copilot(
            prompt="Evaluate independently.",
            model="auto",
            agent="rubber-duck",
            environment={"GITHUB_TOKEN": "token", "PATH": "/usr/bin"},
            runner=runner,
        )
        self.assertIn("--agent=rubber-duck", runner.calls[0][0])
        self.assertEqual(result.agent, "rubber-duck")

    def test_profile_probe_verifies_two_isolated_auto_sessions(self) -> None:
        client = SessionClient()
        report = select_available_profiles(client=client)
        self.assertEqual(report["response_model"], "auto")
        self.assertEqual(report["evaluator_model"], "auto")
        self.assertTrue(report["independent_sessions"])
        self.assertTrue(report["rubric_blind_response"])
        self.assertEqual(report["model_level_independence"], "not-guaranteed-by-auto-selection")
        self.assertEqual(client.calls, [("auto", None), ("auto", None)])

    def test_profile_probe_fails_when_second_session_is_unavailable(self) -> None:
        client = SessionClient(fail_call=2)
        with self.assertRaises(ModelProbeError) as captured:
            select_available_profiles(client=client)
        self.assertEqual(len(captured.exception.probes), 2)

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

    def test_evaluator_runs_in_a_separate_session_and_preserves_observations(self) -> None:
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
        client = FakeCopilotClient(json.dumps(evaluation), model="auto", cli_version="1.2.3")
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
        with patch.dict(os.environ, {"CREATOR_BEHAVIOR_EVALUATOR_MODEL": "auto"}, clear=False):
            result = evaluate_response(payload, client=client)
        self.assertEqual(result["required_observations"][0]["observation"], "route to intake")
        self.assertEqual(result["prohibited_observations"][0]["result"], "ABSENT")
        self.assertIsNone(result["prohibited_observations"][0]["line_start"])
        self.assertIn("independent-session", result["evaluator"])
        self.assertIsNone(client.calls[0]["agent"])


if __name__ == "__main__":
    unittest.main()
