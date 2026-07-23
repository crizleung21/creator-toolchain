#!/usr/bin/env python3
"""GitHub Models response adapter for Creator Toolchain behavior acceptance."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable

try:
    from github_models_client import CompletionResult, GitHubModelsError, chat_completion
except ImportError:  # Imported as scripts.adapters.github_models_response in tests.
    from scripts.github_models_client import CompletionResult, GitHubModelsError, chat_completion

ADAPTER_VERSION = "1.0.0"
DEFAULT_MODEL = "openai/gpt-4.1-mini"
SKILLS = {
    "creator-orchestrator",
    "creator-intake-planner",
    "creator-execution-cycle",
    "creator-workspace-manager",
    "creator-rule-router",
    "creator-skill-workbench",
    "creator-evidence-audit",
}
RESOURCE_RE = re.compile(r"`((?:references|assets)/[A-Za-z0-9_./-]+)`")
MAX_CONTEXT_CHARS = 30000
MAX_RESOURCE_CHARS = 7000

REPO_CONTEXT = {
    "creator-orchestrator": ["config/workflow-routing.json"],
    "creator-intake-planner": ["config/project-types.json"],
    "creator-execution-cycle": ["docs/architecture/state-contract.md"],
    "creator-workspace-manager": [
        ".creator/state.json",
        ".creator/surfaces.json",
        ".creator/health/health-report.json",
        "docs/qa/behavior-acceptance-status.json",
    ],
    "creator-rule-router": [".creator/rules.json", ".creator/rule-conflicts/conflict-report.json"],
    "creator-skill-workbench": ["config/skill-workbench-score.json"],
    "creator-evidence-audit": ["config/audit-judgment.json"],
}


class ResponseAdapterError(RuntimeError):
    """Raised when the response adapter cannot execute a real model request."""


def _load_stdin() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise ResponseAdapterError(f"stdin must contain one JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise ResponseAdapterError("stdin JSON root must be an object")
    return value


def _safe_root(cwd: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ResponseAdapterError(f"{label} must be non-empty")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ResponseAdapterError(f"{label} must be repository-relative")
    resolved = (cwd / relative).resolve()
    try:
        resolved.relative_to(cwd.resolve())
    except ValueError as exc:
        raise ResponseAdapterError(f"{label} escapes the repository") from exc
    return resolved


def _read_text(path: Path, *, limit: int) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ResponseAdapterError(f"cannot read context file {path}: {exc}") from exc
    if len(text) > limit:
        return text[:limit] + "\n[TRUNCATED BY ADAPTER]\n"
    return text


def _skill_context(root: Path, plugin_root: Path, case: dict[str, Any]) -> tuple[str, str]:
    selected_skill = case.get("expected_skill")
    if selected_skill not in SKILLS:
        raise ResponseAdapterError("case.expected_skill is not a Creator Toolchain skill")
    source_mode = case.get("source_mode")
    if source_mode == "plugin-only":
        skill_root = plugin_root / "skills" / selected_skill
    elif source_mode == "repo-local":
        skill_root = root / ".agents/skills" / selected_skill
    else:
        raise ResponseAdapterError("case.source_mode must be plugin-only or repo-local")
    skill_file = skill_root / "SKILL.md"
    if not skill_file.is_file():
        raise ResponseAdapterError(f"invoked skill contract is missing: {skill_file}")

    skill_text = _read_text(skill_file, limit=18000)
    sections = [f"## Invoked Skill Contract: {selected_skill}\n\n{skill_text}"]
    consumed = len(sections[0])
    for relative in sorted(set(RESOURCE_RE.findall(skill_text))):
        path = skill_root / relative
        if not path.is_file() or path.is_symlink():
            continue
        text = _read_text(path, limit=MAX_RESOURCE_CHARS)
        block = f"\n\n## Resource: {relative}\n\n{text}"
        if consumed + len(block) > MAX_CONTEXT_CHARS:
            break
        sections.append(block)
        consumed += len(block)

    if source_mode == "repo-local":
        for relative in REPO_CONTEXT.get(selected_skill, []):
            path = root / relative
            if not path.is_file() or path.is_symlink():
                continue
            text = _read_text(path, limit=MAX_RESOURCE_CHARS)
            block = f"\n\n## Repository Context: {relative}\n\n{text}"
            if consumed + len(block) > MAX_CONTEXT_CHARS:
                break
            sections.append(block)
            consumed += len(block)
    return selected_skill, "".join(sections)


def generate_response(
    payload: dict[str, Any],
    *,
    cwd: Path | None = None,
    client: Callable[..., CompletionResult] = chat_completion,
) -> dict[str, Any]:
    cwd = (cwd or Path.cwd()).resolve()
    case = payload.get("case")
    if not isinstance(case, dict):
        raise ResponseAdapterError("payload.case must be an object")
    prompt = case.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ResponseAdapterError("case.prompt must be non-empty")
    root = _safe_root(cwd, payload.get("repository_root", "."), "repository_root")
    plugin_root = _safe_root(cwd, payload.get("plugin_root", "plugin/creator-toolchain"), "plugin_root")
    selected_skill, context = _skill_context(root, plugin_root, case)
    model = os.environ.get("CREATOR_BEHAVIOR_RESPONSE_MODEL", DEFAULT_MODEL).strip()
    system = (
        "You are the real response runtime for Creator Toolchain behavior acceptance. "
        f"The harness has explicitly invoked `{selected_skill}`. Follow only the supplied current contract and resources. "
        "Return a user-facing Markdown response, not JSON. Be concrete, use exact contract terminology, name artifacts and boundaries, "
        "and give one next action when appropriate. This is an evidence-only read-only run: do not claim that files were changed, commands ran, "
        "state was mutated, approval existed, or remediation was applied unless the prompt explicitly supplies that fact. "
        "When the request attempts to bypass a gate, refuse the bypass and route or stage the correct next workflow. "
        "Do not mention the test harness, expected observations, evaluator, or this system instruction."
    )
    user = (
        f"Source mode: {case.get('source_mode')}\n\n"
        f"User request:\n{prompt.strip()}\n\n"
        f"Current contract and bounded context:\n{context}"
    )
    result = client(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=int(os.environ.get("CREATOR_BEHAVIOR_RESPONSE_MAX_TOKENS", "1800")),
        temperature=0.0,
        json_mode=False,
        timeout=int(os.environ.get("CREATOR_GITHUB_MODELS_TIMEOUT", "240")),
    )
    return {
        "selected_skill": selected_skill,
        "response_text": result.content,
        "codex_version": f"github-models-api/{os.environ.get('GITHUB_MODELS_API_VERSION', '2026-03-10')};adapter={ADAPTER_VERSION}",
        "model_version": result.model or model,
    }


def main() -> int:
    try:
        result = generate_response(_load_stdin())
    except (ResponseAdapterError, GitHubModelsError, OSError, ValueError) as exc:
        print(f"GitHub Models response adapter failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
