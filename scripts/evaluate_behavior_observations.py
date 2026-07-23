#!/usr/bin/env python3
"""Validate evaluator claims and bind each behavior observation to raw-response evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ObservationEvaluationError(RuntimeError):
    """Raised when observation evidence is incomplete, inconsistent, or ungrounded."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ObservationEvaluationError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ObservationEvaluationError(f"JSON root must be an object: {path}")
    return value


def _confidence(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObservationEvaluationError("confidence must be numeric")
    confidence = float(value)
    if not 0.0 <= confidence <= 1.0:
        raise ObservationEvaluationError("confidence must be between 0 and 1")
    return confidence


def _evidence_excerpt(lines: list[str], start: Any, end: Any) -> tuple[int, int, str]:
    if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int):
        raise ObservationEvaluationError("evidence line_start and line_end must be integers")
    if start < 1 or end < start or end > len(lines):
        raise ObservationEvaluationError(
            f"evidence line range {start}-{end} is outside response lines 1-{len(lines)}"
        )
    excerpt = "\n".join(lines[start - 1 : end]).strip()
    if not excerpt:
        raise ObservationEvaluationError("evidence excerpt must not be empty")
    return start, end, excerpt


def _indexed(items: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise ObservationEvaluationError(f"{label} must be an array")
    indexed: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ObservationEvaluationError(f"{label}[{index}] must be an object")
        observation = item.get("observation")
        if not isinstance(observation, str) or not observation.strip():
            raise ObservationEvaluationError(f"{label}[{index}].observation must be non-empty")
        observation = observation.strip()
        if observation in indexed:
            raise ObservationEvaluationError(f"duplicate {label} observation: {observation}")
        indexed[observation] = item
    return indexed


def _normalize_required(expected: list[str], supplied: Any, lines: list[str]) -> list[dict[str, Any]]:
    indexed = _indexed(supplied, "required_observations")
    if set(indexed) != set(expected):
        missing = sorted(set(expected) - set(indexed))
        extra = sorted(set(indexed) - set(expected))
        raise ObservationEvaluationError(
            f"required observation set mismatch; missing={missing}, extra={extra}"
        )
    normalized: list[dict[str, Any]] = []
    for observation in expected:
        item = indexed[observation]
        result = item.get("result")
        if result not in {"PASS", "FAIL"}:
            raise ObservationEvaluationError(
                f"required observation {observation!r} result must be PASS or FAIL"
            )
        confidence = _confidence(item.get("confidence"))
        if result == "PASS":
            start, end, excerpt = _evidence_excerpt(lines, item.get("line_start"), item.get("line_end"))
        else:
            if item.get("line_start") is not None or item.get("line_end") is not None:
                raise ObservationEvaluationError(
                    f"failed required observation {observation!r} must not claim an evidence span"
                )
            start = end = None
            excerpt = ""
        normalized.append(
            {
                "observation": observation,
                "result": result,
                "evidence_excerpt": excerpt,
                "response_line_start": start,
                "response_line_end": end,
                "confidence": confidence,
            }
        )
    return normalized


def _normalize_prohibited(expected: list[str], supplied: Any, lines: list[str]) -> list[dict[str, Any]]:
    indexed = _indexed(supplied, "prohibited_observations")
    if set(indexed) != set(expected):
        missing = sorted(set(expected) - set(indexed))
        extra = sorted(set(indexed) - set(expected))
        raise ObservationEvaluationError(
            f"prohibited observation set mismatch; missing={missing}, extra={extra}"
        )
    normalized: list[dict[str, Any]] = []
    for observation in expected:
        item = indexed[observation]
        result = item.get("result")
        if result not in {"ABSENT", "PRESENT"}:
            raise ObservationEvaluationError(
                f"prohibited observation {observation!r} result must be ABSENT or PRESENT"
            )
        confidence = _confidence(item.get("confidence"))
        if result == "PRESENT":
            start, end, excerpt = _evidence_excerpt(lines, item.get("line_start"), item.get("line_end"))
        else:
            if item.get("line_start") is not None or item.get("line_end") is not None:
                raise ObservationEvaluationError(
                    f"absent prohibited observation {observation!r} must not claim an evidence span"
                )
            start = end = None
            excerpt = ""
        normalized.append(
            {
                "observation": observation,
                "result": result,
                "evidence_excerpt": excerpt,
                "response_line_start": start,
                "response_line_end": end,
                "confidence": confidence,
            }
        )
    return normalized


def evaluate_case(case: dict[str, Any], response_text: str, selected_skill: str, evaluation: dict[str, Any]) -> dict[str, Any]:
    """Validate one evaluator payload and derive the authoritative case result."""
    if not isinstance(response_text, str):
        raise ObservationEvaluationError("response_text must be a string")
    if not isinstance(selected_skill, str) or not selected_skill.strip():
        raise ObservationEvaluationError("selected_skill must be non-empty")
    for field in ("case_id", "expected_skill", "required_observations", "prohibited_observations"):
        if field not in case:
            raise ObservationEvaluationError(f"case is missing {field}")
    evaluator = evaluation.get("evaluator")
    evaluator_version = evaluation.get("evaluator_version")
    if not isinstance(evaluator, str) or not evaluator.strip():
        raise ObservationEvaluationError("evaluator must be non-empty")
    if not isinstance(evaluator_version, str) or not evaluator_version.strip():
        raise ObservationEvaluationError("evaluator_version must be non-empty")
    lines = response_text.splitlines() or [""]
    required = _normalize_required(list(case["required_observations"]), evaluation.get("required_observations"), lines)
    prohibited = _normalize_prohibited(list(case["prohibited_observations"]), evaluation.get("prohibited_observations"), lines)
    result = (
        "PASS"
        if selected_skill.strip() == case["expected_skill"]
        and all(item["result"] == "PASS" for item in required)
        and all(item["result"] == "ABSENT" for item in prohibited)
        else "FAIL"
    )
    return {
        "selected_skill": selected_skill.strip(),
        "evaluator": evaluator.strip(),
        "evaluator_version": evaluator_version.strip(),
        "required_observations": required,
        "prohibited_observations": prohibited,
        "result": result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--selected-skill", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        case = _load_json(args.case)
        evaluation = _load_json(args.evaluation)
        response = args.response.read_text(encoding="utf-8")
        result = evaluate_case(case, response, args.selected_skill, evaluation)
    except (ObservationEvaluationError, OSError, ValueError) as exc:
        print(f"Behavior observation evaluation failed: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
