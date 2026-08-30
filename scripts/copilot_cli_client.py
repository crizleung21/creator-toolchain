#!/usr/bin/env python3
"""Locked-down programmatic client for GitHub Copilot CLI behavior adapters."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

TOKEN_ENVIRONMENTS = ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
SAFE_MODEL_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class CopilotCLIError(RuntimeError):
    """Raised when Copilot CLI cannot return one trustworthy text response."""


@dataclass(frozen=True)
class CopilotResult:
    content: str
    model: str
    cli_version: str


def _token_available(environment: Mapping[str, str]) -> bool:
    return any(environment.get(name, "").strip() for name in TOKEN_ENVIRONMENTS)


def _version(
    binary: str,
    *,
    environment: Mapping[str, str],
    timeout: int,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> str:
    try:
        process = runner(
            [binary, "version"],
            text=True,
            capture_output=True,
            timeout=min(timeout, 60),
            check=False,
            env=dict(environment),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CopilotCLIError(f"cannot execute Copilot CLI version check: {exc}") from exc
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise CopilotCLIError(f"Copilot CLI version check exited {process.returncode}: {detail}")
    text = (process.stdout or process.stderr).strip()
    if not text:
        raise CopilotCLIError("Copilot CLI version output is empty")
    return text.splitlines()[0].strip()


def run_copilot(
    *,
    prompt: str,
    model: str,
    timeout: int = 420,
    binary: str = "copilot",
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    environment: Mapping[str, str] | None = None,
) -> CopilotResult:
    """Run one no-tools Copilot CLI prompt and return only the agent response."""

    if not isinstance(prompt, str) or not prompt.strip():
        raise CopilotCLIError("prompt must be non-empty")
    if not isinstance(model, str) or not SAFE_MODEL_RE.fullmatch(model.strip()):
        raise CopilotCLIError("model contains unsupported characters")
    if timeout < 1:
        raise CopilotCLIError("timeout must be positive")

    base_environment = dict(os.environ if environment is None else environment)
    if not _token_available(base_environment):
        raise CopilotCLIError(
            "Copilot CLI authentication is unavailable; set COPILOT_GITHUB_TOKEN, GH_TOKEN, or GITHUB_TOKEN"
        )
    if shutil.which(binary, path=base_environment.get("PATH")) is None and runner is subprocess.run:
        raise CopilotCLIError(f"Copilot CLI executable is unavailable: {binary}")

    with tempfile.TemporaryDirectory(prefix="creator-copilot-cli-") as directory:
        workdir = Path(directory).resolve()
        home = workdir / "copilot-home"
        home.mkdir()
        child_environment = dict(base_environment)
        child_environment["COPILOT_HOME"] = str(home)
        child_environment["COPILOT_MODEL"] = model.strip()
        child_environment["NO_COLOR"] = "1"
        child_environment["COPILOT_OTEL_ENABLED"] = "false"

        # Keep the invocation compatible with the released CLI while denying every
        # tool class the behavior adapter does not need. All source context is
        # embedded in the prompt and the process runs in an empty temporary root.
        argv: Sequence[str] = (
            binary,
            "-p",
            prompt.strip(),
            "-s",
            f"--model={model.strip()}",
            "--no-ask-user",
            "--no-custom-instructions",
            "--disable-builtin-mcps",
            "--deny-tool=shell,write,read,url,memory",
            "-C",
            str(workdir),
        )
        try:
            process = runner(
                list(argv),
                cwd=workdir,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                env=child_environment,
            )
        except subprocess.TimeoutExpired as exc:
            raise CopilotCLIError(f"Copilot CLI timed out after {timeout} seconds") from exc
        except OSError as exc:
            raise CopilotCLIError(f"cannot execute Copilot CLI: {exc}") from exc

        if process.returncode != 0:
            detail = (process.stderr or process.stdout).strip()
            raise CopilotCLIError(f"Copilot CLI exited {process.returncode}: {detail[:2000]}")
        content = process.stdout.strip()
        if not content:
            raise CopilotCLIError("Copilot CLI response is empty")
        cli_version = _version(
            binary,
            environment=child_environment,
            timeout=timeout,
            runner=runner,
        )
        return CopilotResult(content=content, model=model.strip(), cli_version=cli_version)
