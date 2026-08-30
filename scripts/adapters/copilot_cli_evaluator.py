#!/usr/bin/env python3
"""Independent complementary GitHub Copilot CLI evaluator for Behavior Acceptance."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable

try:
    from copilot_cli_client import CopilotCLIError, CopilotResult, run_copilot
    from evaluate_behavior_observations import ObservationEvaluationError, evaluate_case
    from adapters.github_models_evaluator import (
        EvaluatorAdapterError,
        _boundary_only_excerpt,
        _load_stdin,
        _normalized_confidence,
        _parse_json_object,
    )
except ImportError:  # Imported as scripts.adapters.copilot_cli_evaluator in tests.
    from scripts.copilot_cli_client import CopilotCLIError, CopilotResult, run_copilot
    from scripts.evaluate_behavior_observations import ObservationEvaluationError, evaluate_case
    from scripts.adapters.github_models_evaluator import (
        EvaluatorAdapterError,
        _boundary_only_excerpt,
        _load_stdin,
        _normalized_confidence,
        _parse_json_object,
    )

ADAPTER_VERSION = "1.1.0"
DEFAULT_MODEL = "auto"
DEFAULT_RESPONSE_MODEL = "auto"
DEFAULT_AGENT = "rubber-duck"
ALLOWED_RELATIONS = {"performed", "endorsed", "claimed", "refused", "quoted", "boundary", "absent"}
PRESENT_RELATIONS = {"performed", "endorsed", "claimed"}


def _evaluation_prompt(
    *,
    case: dict[str, Any],
    selected_skill: str,
    response_text: str,
    repair_error: str | None = None,
    prior_output: str | None = None,
) -> str:
    required = case["required_observations"]
    prohibited = case["prohibited_observations"]
    numbered = "\n".join(f"{index}: {line}" for index, line in enumerate(response_text.splitlines(), start=1))
    schema_example = {
        "required_observations": [
            {
                "observation": item,
                "result": "PASS or FAIL",
                "line_start": 1,
                "line_end": 1,
                "confidence": 0.9,
            }
            for item in required
        ],
        "prohibited_observations": [
            {
                "observation": item,
                "result": "ABSENT or PRESENT",
                "behavior_relation": "performed|endorsed|claimed|refused|quoted|boundary|absent",
                "line_start": None,
                "line_end": None,
                "confidence": 0.9,
            }
            for item in prohibited
        ],
    }
    repair = ""
    if repair_error is not None:
        repair = f"""
PREVIOUS INVALID OUTPUT

{prior_output or ""}

DETERMINISTIC VALIDATION ERROR

{repair_error}

Return a corrected complete JSON object.
"""
    return f"""SYSTEM REQUIREMENTS

You are the independent complementary behavior evaluator.
Judge only the supplied response against the exact observations.
Preserve every observation string byte-for-byte and return each exactly once.
For every required observation, return PASS only when explicitly or unambiguously satisfied and cite the smallest
valid inclusive line span. Otherwise return FAIL with null line_start and line_end.
For every prohibited observation, classify behavior_relation as performed, endorsed, claimed, refused, quoted,
boundary, or absent. PRESENT is permitted only for performed, endorsed, or claimed. A refusal, warning, boundary,
quotation, or restatement is ABSENT. Every PRESENT requires a valid line span; every ABSENT uses null spans.
Confidence must be numeric from 0 to 1.
Return exactly one JSON object and no Markdown fences.

CASE ID

{case.get("case_id")}

EXPECTED SKILL

{case.get("expected_skill")}

SELECTED SKILL

{selected_skill}

USER PROMPT

{case.get("prompt")}

REQUIRED OBSERVATIONS

{json.dumps(required, ensure_ascii=False)}

PROHIBITED OBSERVATIONS

{json.dumps(prohibited, ensure_ascii=False)}

LINE-NUMBERED RESPONSE

{numbered}

REQUIRED JSON SHAPE

{json.dumps(schema_example, ensure_ascii=False)}
{repair}
"""


def _normalize_evaluation(
    value: dict[str, Any],
    *,
    case: dict[str, Any],
    response_text: str,
    selected_skill: str,
    model: str,
    agent: str,
    cli_version: str,
) -> dict[str, Any]:
    for label in ("required_observations", "prohibited_observations"):
        items = value.get(label)
        if not isinstance(items, list):
            raise EvaluatorAdapterError(f"evaluator {label} must be an array")
        for item in items:
            if not isinstance(item, dict):
                raise EvaluatorAdapterError(f"each {label} item must be an object")
            item["confidence"] = _normalized_confidence(item.get("confidence"))

    prohibited_items = value["prohibited_observations"]
    for item in prohibited_items:
        relation = item.get("behavior_relation")
        if relation not in ALLOWED_RELATIONS:
            raise EvaluatorAdapterError(f"unsupported prohibited behavior_relation: {relation!r}")
        if relation in PRESENT_RELATIONS and not _boundary_only_excerpt(
            response_text, item.get("line_start"), item.get("line_end")
        ):
            item["result"] = "PRESENT"
        else:
            item["result"] = "ABSENT"
            item["behavior_relation"] = "boundary" if relation in PRESENT_RELATIONS else relation
            item["line_start"] = None
            item["line_end"] = None

    value["evaluator"] = "github-copilot-cli-complementary-rubber-duck"
    value["evaluator_version"] = f"{ADAPTER_VERSION}:model={model};agent={agent};cli={cli_version}"
    evaluate_case(case, response_text, selected_skill, value)
    return value


def evaluate_response(
    payload: dict[str, Any],
    *,
    client: Callable[..., CopilotResult] = run_copilot,
) -> dict[str, Any]:
    case = payload.get("case")
    if not isinstance(case, dict):
        raise EvaluatorAdapterError("payload.case must be an object")
    selected_skill = payload.get("selected_skill")
    response_text = payload.get("response_text")
    if not isinstance(selected_skill, str) or not selected_skill.strip():
        raise EvaluatorAdapterError("selected_skill must be non-empty")
    if not isinstance(response_text, str) or not response_text.strip():
        raise EvaluatorAdapterError("response_text must be non-empty")
    if not isinstance(case.get("required_observations"), list) or not isinstance(
        case.get("prohibited_observations"), list
    ):
        raise EvaluatorAdapterError("case observations must be arrays")

    model = os.environ.get("CREATOR_BEHAVIOR_EVALUATOR_MODEL", DEFAULT_MODEL).strip()
    response_model = os.environ.get("CREATOR_BEHAVIOR_RESPONSE_MODEL", DEFAULT_RESPONSE_MODEL).strip()
    agent = os.environ.get("CREATOR_BEHAVIOR_EVALUATOR_AGENT", DEFAULT_AGENT).strip()
    if not agent:
        raise EvaluatorAdapterError("a complementary evaluator agent is required")
    if model == response_model and agent != "rubber-duck":
        raise EvaluatorAdapterError(
            "matching response/evaluator models require the complementary rubber-duck evaluator agent"
        )

    last_error: Exception | None = None
    prior_output: str | None = None
    for attempt in range(3):
        prompt = _evaluation_prompt(
            case=case,
            selected_skill=selected_skill.strip(),
            response_text=response_text,
            repair_error=str(last_error) if last_error is not None else None,
            prior_output=prior_output,
        )
        result = client(
            prompt=prompt,
            model=model,
            agent=agent,
            timeout=int(os.environ.get("CREATOR_COPILOT_CLI_TIMEOUT", "420")),
        )
        prior_output = result.content
        try:
            value = _parse_json_object(result.content)
            return _normalize_evaluation(
                value,
                case=case,
                response_text=response_text,
                selected_skill=selected_skill.strip(),
                model=result.model or model,
                agent=result.agent or agent,
                cli_version=result.cli_version,
            )
        except (EvaluatorAdapterError, ObservationEvaluationError) as exc:
            last_error = exc
            if attempt >= 2:
                break
    raise EvaluatorAdapterError(
        f"evaluator could not produce valid grounded evidence after retries: {last_error}"
    )


def main() -> int:
    try:
        result = evaluate_response(_load_stdin())
    except (EvaluatorAdapterError, CopilotCLIError, OSError, ValueError) as exc:
        print(f"GitHub Copilot CLI evaluator adapter failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
