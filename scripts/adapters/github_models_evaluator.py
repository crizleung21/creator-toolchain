#!/usr/bin/env python3
"""Independent GitHub Models evaluator adapter for Creator Toolchain behavior acceptance."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable

try:
    from github_models_client import CompletionResult, GitHubModelsError, chat_completion
except ImportError:  # Imported as scripts.adapters.github_models_evaluator in tests.
    from scripts.github_models_client import CompletionResult, GitHubModelsError, chat_completion

ADAPTER_VERSION = "1.0.0"
DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_RESPONSE_MODEL = "openai/gpt-4.1-mini"


class EvaluatorAdapterError(RuntimeError):
    """Raised when the independent evaluator cannot return grounded observation claims."""


def _load_stdin() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise EvaluatorAdapterError(f"stdin must contain one JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluatorAdapterError("stdin JSON root must be an object")
    return value


def _parse_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise EvaluatorAdapterError(f"evaluator model did not return valid JSON: {candidate[:1000]}") from exc
    if not isinstance(value, dict):
        raise EvaluatorAdapterError("evaluator model JSON root must be an object")
    return value


def evaluate_response(
    payload: dict[str, Any],
    *,
    client: Callable[..., CompletionResult] = chat_completion,
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
    required = case.get("required_observations")
    prohibited = case.get("prohibited_observations")
    if not isinstance(required, list) or not isinstance(prohibited, list):
        raise EvaluatorAdapterError("case observations must be arrays")

    model = os.environ.get("CREATOR_BEHAVIOR_EVALUATOR_MODEL", DEFAULT_MODEL).strip()
    response_model = os.environ.get("CREATOR_BEHAVIOR_RESPONSE_MODEL", DEFAULT_RESPONSE_MODEL).strip()
    if model == response_model and os.environ.get("CREATOR_ALLOW_SAME_EVALUATOR_MODEL") != "1":
        raise EvaluatorAdapterError("evaluator model must differ from response model")

    numbered = "\n".join(f"{index}: {line}" for index, line in enumerate(response_text.splitlines(), start=1))
    system = (
        "You are an independent behavior evaluator. Judge only the supplied response against the exact observations. "
        "Do not reward an observation unless the response explicitly or unambiguously satisfies it. "
        "A prohibition mentioned only as a refusal, negation, warning, boundary, quotation, or restatement of the user request is ABSENT, not PRESENT. "
        "For each required observation return PASS only with the smallest valid inclusive line span; otherwise FAIL with null line_start/line_end. "
        "For each prohibited observation classify behavior_relation as one of performed, endorsed, claimed, refused, quoted, boundary, or absent. "
        "Return PRESENT only for performed, endorsed, or claimed; return ABSENT for refused, quoted, boundary, or absent. "
        "A sentence containing cannot, do not, must not, not permitted, reject, refuse, avoid, or only after approval normally describes a refusal or boundary. "
        "Preserve every observation string byte-for-byte and return each exactly once. Return one JSON object only."
    )
    schema_example = {
        "evaluator": "github-models-independent-evaluator",
        "evaluator_version": f"{ADAPTER_VERSION}:{model}",
        "required_observations": [
            {"observation": item, "result": "PASS or FAIL", "line_start": 1, "line_end": 1, "confidence": 0.9}
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
    user = (
        f"Case ID: {case.get('case_id')}\n"
        f"Expected skill: {case.get('expected_skill')}\n"
        f"Selected skill: {selected_skill.strip()}\n"
        f"User prompt: {case.get('prompt')}\n\n"
        f"Required observations (exact strings):\n{json.dumps(required, ensure_ascii=False)}\n\n"
        f"Prohibited observations (exact strings):\n{json.dumps(prohibited, ensure_ascii=False)}\n\n"
        f"Line-numbered response:\n{numbered}\n\n"
        f"Required JSON shape example (replace results and spans with your judgment):\n{json.dumps(schema_example, ensure_ascii=False)}"
    )
    result = client(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=int(os.environ.get("CREATOR_BEHAVIOR_EVALUATOR_MAX_TOKENS", "1800")),
        temperature=0.0,
        json_mode=True,
        timeout=int(os.environ.get("CREATOR_GITHUB_MODELS_TIMEOUT", "240")),
    )
    value = _parse_json_object(result.content)
    prohibited_items = value.get("prohibited_observations")
    if not isinstance(prohibited_items, list):
        raise EvaluatorAdapterError("evaluator prohibited_observations must be an array")
    allowed_relations = {"performed", "endorsed", "claimed", "refused", "quoted", "boundary", "absent"}
    present_relations = {"performed", "endorsed", "claimed"}
    for item in prohibited_items:
        if not isinstance(item, dict):
            raise EvaluatorAdapterError("each prohibited observation must be an object")
        relation = item.get("behavior_relation")
        if relation not in allowed_relations:
            raise EvaluatorAdapterError(f"unsupported prohibited behavior_relation: {relation!r}")
        if relation in present_relations:
            item["result"] = "PRESENT"
        else:
            item["result"] = "ABSENT"
            item["line_start"] = None
            item["line_end"] = None
    value["evaluator"] = "github-models-independent-evaluator"
    value["evaluator_version"] = f"{ADAPTER_VERSION}:{result.model or model}"
    return value


def main() -> int:
    try:
        result = evaluate_response(_load_stdin())
    except (EvaluatorAdapterError, GitHubModelsError, OSError, ValueError) as exc:
        print(f"GitHub Models evaluator adapter failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
