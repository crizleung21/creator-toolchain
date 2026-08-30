#!/usr/bin/env python3
"""Verify the two independent Copilot CLI execution profiles used by Behavior QA."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

try:
    from copilot_cli_client import CopilotCLIError, CopilotResult, run_copilot
except ImportError:  # Imported as scripts.probe_copilot_models in tests.
    from scripts.copilot_cli_client import CopilotCLIError, CopilotResult, run_copilot

PROBE_PROMPT = "Reply with exactly OK and no other text."
PROFILES = (
    {"role": "response", "model": "auto", "agent": None},
    {"role": "evaluator", "model": "auto", "agent": "rubber-duck"},
)


class ModelProbeError(RuntimeError):
    """Raised when either independent Copilot execution profile is unavailable."""

    def __init__(self, message: str, probes: list[dict[str, object]]) -> None:
        super().__init__(message)
        self.probes = probes


def select_available_profiles(
    *,
    client: Callable[..., CopilotResult] = run_copilot,
    timeout: int = 120,
) -> dict[str, object]:
    """Probe Auto plus the complementary rubber-duck evaluator profile."""

    probes: list[dict[str, object]] = []
    results: dict[str, CopilotResult] = {}
    for profile in PROFILES:
        role = str(profile["role"])
        model = str(profile["model"])
        agent = profile["agent"]
        try:
            result = client(
                prompt=PROBE_PROMPT,
                model=model,
                agent=agent if isinstance(agent, str) else None,
                timeout=timeout,
            )
            if not result.content.strip():
                raise CopilotCLIError("probe response is empty")
            probes.append(
                {
                    "role": role,
                    "model": model,
                    "agent": agent,
                    "status": "PASS",
                    "cli_version": result.cli_version,
                    "response_excerpt": result.content.strip()[:120],
                }
            )
            results[role] = result
        except (CopilotCLIError, OSError, ValueError) as exc:
            probes.append(
                {
                    "role": role,
                    "model": model,
                    "agent": agent,
                    "status": "UNAVAILABLE",
                    "error": str(exc)[:2000],
                }
            )
    if set(results) != {"response", "evaluator"}:
        raise ModelProbeError(
            "response Auto or complementary rubber-duck evaluator profile is unavailable",
            probes,
        )
    return {
        "schema_version": "1.0.0",
        "status": "PASS",
        "response_model": "auto",
        "response_agent": None,
        "evaluator_model": "auto",
        "evaluator_agent": "rubber-duck",
        "distinct_execution_profiles": True,
        "complementary_evaluator": True,
        "cli_version": results["response"].cli_version,
        "probes": probes,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def _write_report(path: Path | None, report: dict[str, object]) -> None:
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report = select_available_profiles(timeout=args.timeout)
    except ModelProbeError as exc:
        report = {
            "schema_version": "1.0.0",
            "status": "FAIL",
            "error": str(exc),
            "probes": exc.probes,
        }
        _write_report(args.output, report)
        print(f"Copilot execution-profile probe failed: {exc}", file=sys.stderr)
        return 2
    _write_report(args.output, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
