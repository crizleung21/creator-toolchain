#!/usr/bin/env python3
"""Dependency-free GitHub Models chat-completion client with bounded retries."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

DEFAULT_ENDPOINT = "https://models.github.ai/inference/chat/completions"
DEFAULT_API_VERSION = "2026-03-10"
RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


class GitHubModelsError(RuntimeError):
    """Raised when GitHub Models inference cannot return a trustworthy response."""


@dataclass(frozen=True)
class CompletionResult:
    content: str
    model: str
    response_id: str
    usage: dict[str, Any]


def _token() -> str:
    value = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not value or not value.strip():
        raise GitHubModelsError("GITHUB_TOKEN or GH_TOKEN is required for GitHub Models")
    return value.strip()


def _retry_delay(headers: Any, attempt: int) -> float:
    retry_after = headers.get("Retry-After") if headers is not None else None
    if retry_after:
        try:
            return max(1.0, min(120.0, float(retry_after)))
        except ValueError:
            pass
    reset = headers.get("X-RateLimit-Reset") if headers is not None else None
    if reset:
        try:
            return max(1.0, min(120.0, float(reset) - time.time()))
        except ValueError:
            pass
    return min(60.0, float(2 ** min(attempt, 6)))


def chat_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int = 1800,
    temperature: float = 0.0,
    json_mode: bool = False,
    timeout: int = 180,
    attempts: int = 8,
    endpoint: str | None = None,
    api_version: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> CompletionResult:
    """Call GitHub Models and return one non-streaming assistant message."""

    if not isinstance(model, str) or not model.strip():
        raise GitHubModelsError("model must be non-empty")
    if not isinstance(messages, list) or not messages:
        raise GitHubModelsError("messages must be a non-empty array")
    if not all(isinstance(item, dict) and item.get("role") and isinstance(item.get("content"), str) for item in messages):
        raise GitHubModelsError("every message must contain role and string content")
    if attempts < 1:
        raise GitHubModelsError("attempts must be positive")

    payload: dict[str, Any] = {
        "model": model.strip(),
        "messages": messages,
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = endpoint or os.environ.get("GITHUB_MODELS_ENDPOINT", DEFAULT_ENDPOINT)
    version = api_version or os.environ.get("GITHUB_MODELS_API_VERSION", DEFAULT_API_VERSION)
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
        "User-Agent": "creator-toolchain-behavior-harness/1.1.0",
        "X-GitHub-Api-Version": version,
    }

    last_error: Exception | None = None
    for attempt in range(attempts):
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = GitHubModelsError(f"GitHub Models HTTP {exc.code}: {detail[:1000]}")
            if exc.code not in RETRYABLE_STATUS or attempt + 1 >= attempts:
                raise last_error from exc
            sleep(_retry_delay(exc.headers, attempt))
            continue
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                raise GitHubModelsError(f"GitHub Models request failed: {exc}") from exc
            sleep(_retry_delay(None, attempt))
            continue

        try:
            value = json.loads(raw)
            choice = value["choices"][0]
            content = choice["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise GitHubModelsError(f"GitHub Models returned an invalid response: {raw[:1000]}") from exc
        if not isinstance(content, str) or not content.strip():
            raise GitHubModelsError("GitHub Models returned an empty assistant message")
        response_model = value.get("model") if isinstance(value.get("model"), str) else model.strip()
        response_id = value.get("id") if isinstance(value.get("id"), str) else "unknown"
        usage = value.get("usage") if isinstance(value.get("usage"), dict) else {}
        return CompletionResult(content=content.strip(), model=response_model, response_id=response_id, usage=usage)

    raise GitHubModelsError(f"GitHub Models request failed after retries: {last_error}")
