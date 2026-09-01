#!/usr/bin/env python3
"""Independent exact-evidence evaluator for deterministic contract responses."""

from __future__ import annotations

import json
import sys
from typing import Any

EVALUATOR_VERSION = "1.0.0"
NEGATION_MARKERS = (
    "cannot ", "can not ", "do not ", "don't ", "must not ", "not permitted",
    "not allowed", "refuse ", "reject ", "without ", "remains unchanged",
)


class ContractEvaluatorError(RuntimeError):
    pass


def _load() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise ContractEvaluatorError(f"stdin must contain one JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractEvaluatorError("stdin JSON root must be an object")
    return value


def _line_for(lines: list[str], phrase: str) -> int | None:
    needle = phrase.casefold()
    for index, line in enumerate(lines, start=1):
        if needle in line.casefold():
            return index
    return None


def _prohibited_present(lines: list[str], phrase: str) -> int | None:
    needle = phrase.casefold()
    for index, line in enumerate(lines, start=1):
        folded = line.casefold()
        if needle not in folded:
            continue
        prefix = folded[: folded.index(needle)]
        if any(marker in prefix[-80:] for marker in NEGATION_MARKERS):
            continue
        return index
    return None


def evaluate_response(payload: dict[str, Any]) -> dict[str, Any]:
    case = payload.get("case")
    response_text = payload.get("response_text")
    if not isinstance(case, dict):
        raise ContractEvaluatorError("payload.case must be an object")
    if not isinstance(response_text, str) or not response_text.strip():
        raise ContractEvaluatorError("response_text must be non-empty")
    required = case.get("required_observations")
    prohibited = case.get("prohibited_observations")
    if not isinstance(required, list) or not isinstance(prohibited, list):
        raise ContractEvaluatorError("case observations must be arrays")
    lines = response_text.splitlines()
    required_results = []
    for observation in required:
        line = _line_for(lines, str(observation))
        required_results.append({
            "observation": observation,
            "result": "PASS" if line is not None else "FAIL",
            "line_start": line,
            "line_end": line,
            "confidence": 1.0,
        })
    prohibited_results = []
    for observation in prohibited:
        line = _prohibited_present(lines, str(observation))
        prohibited_results.append({
            "observation": observation,
            "result": "PRESENT" if line is not None else "ABSENT",
            "line_start": line,
            "line_end": line,
            "confidence": 1.0,
        })
    return {
        "evaluator": "deterministic-contract-evaluator",
        "evaluator_version": EVALUATOR_VERSION,
        "required_observations": required_results,
        "prohibited_observations": prohibited_results,
    }


def main() -> int:
    try:
        result = evaluate_response(_load())
    except (ContractEvaluatorError, OSError, ValueError) as exc:
        print(f"Deterministic contract evaluation failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
