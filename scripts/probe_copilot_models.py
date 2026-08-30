#!/usr/bin/env python3
"""Select two distinct Copilot CLI models that can complete a locked-down probe."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Iterable

try:
    from copilot_cli_client import CopilotCLIError, CopilotResult, run_copilot
except ImportError:  # Imported as scripts.probe_copilot_models in tests.
    from scripts.copilot_cli_client import CopilotCLIError, CopilotResult, run_copilot

DEFAULT_CANDIDATES = (
    "claude-sonnet-4.6",
    "claude-haiku-4.5",
    "gpt-5.3-codex",
    "gpt-5.2",
    "gpt-5.1",
    "claude-sonnet-4.5",
    "gemini-3.1-pro-preview",
    "gemini-3.5-flash",
)
PROBE_PROMPT = "Reply with exactly OK and no other text."


class ModelProbeError(RuntimeError):
    """Raised when two distinct available Copilot models cannot be selected."""


def _ordered_unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def select_available_models(
    candidates: Iterable[str] = DEFAULT_CANDIDATES,
    *,
    client: Callable[..., CopilotResult] = run_copilot,
    timeout: int = 120,
) -> dict[str, object]:
    """Probe candidates in order and return the first two distinct successes."""

    ordered = _ordered_unique(candidates)
    if len(ordered) < 2:
        raise ModelProbeError("at least two distinct candidate models are required")
    probes: list[dict[str, object]] = []
    available: list[CopilotResult] = []
    for model in ordered:
        try:
            result = client(prompt=PROBE_PROMPT, model=model, timeout=timeout)
            if not result.content.strip():
                raise CopilotCLIError("probe response is empty")
            probes.append(
                {
                    "model": model,
                    "status": "PASS",
                    "cli_version": result.cli_version,
                    "response_excerpt": result.content.strip()[:120],
                }
            )
            available.append(result)
            if len(available) == 2:
                break
        except (CopilotCLIError, OSError, ValueError) as exc:
            probes.append({"model": model, "status": "UNAVAILABLE", "error": str(exc)[:1000]})
    if len(available) < 2:
        tested = ", ".join(item["model"] for item in probes)
        raise ModelProbeError(f"fewer than two Copilot models were available; tested: {tested}")
    response_model = available[0].model
    evaluator_model = available[1].model
    if response_model == evaluator_model:
        raise ModelProbeError("response and evaluator models must be distinct")
    return {
        "schema_version": "1.0.0",
        "status": "PASS",
        "response_model": response_model,
        "evaluator_model": evaluator_model,
        "distinct_models": True,
        "cli_version": available[0].cli_version,
        "probes": probes,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report = select_available_models(
            args.candidate or DEFAULT_CANDIDATES,
            timeout=args.timeout,
        )
    except ModelProbeError as exc:
        print(f"Copilot model probe failed: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
