#!/usr/bin/env python3
"""Validate a focused GitHub Actions behavior-run artifact before full promotion."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class FocusedBehaviorGateError(RuntimeError):
    """Raised when focused evidence cannot authorize a full promotion run."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FocusedBehaviorGateError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FocusedBehaviorGateError(f"JSON root must be an object: {path}")
    return value


def _request_json(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "User-Agent": "creator-toolchain-focused-behavior-gate", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            value = json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise FocusedBehaviorGateError(f"GitHub API request failed for {url}: {exc}") from exc
    if not isinstance(value, dict):
        raise FocusedBehaviorGateError(f"GitHub API response must be an object: {url}")
    return value


def _download(url: str, token: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "User-Agent": "creator-toolchain-focused-behavior-gate", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    except urllib.error.URLError as exc:
        raise FocusedBehaviorGateError(f"artifact download failed: {exc}") from exc


def _safe_extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise FocusedBehaviorGateError(f"unsafe artifact member: {member.filename}")
            target = (destination / member_path).resolve()
            try:
                target.relative_to(destination.resolve())
            except ValueError as exc:
                raise FocusedBehaviorGateError(f"artifact member escapes destination: {member.filename}") from exc
        bundle.extractall(destination)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find_report(extracted: Path) -> Path:
    candidates = [path for path in sorted(extracted.rglob("report.json")) if "behavior" in path.as_posix().casefold()]
    if len(candidates) != 1:
        raise FocusedBehaviorGateError(f"expected exactly one behavior report.json, found {[path.as_posix() for path in candidates]}")
    return candidates[0]


def _resolve_raw_response(extracted: Path, record: dict[str, Any]) -> Path:
    raw_relative = record.get("raw_response_path")
    if not isinstance(raw_relative, str) or not raw_relative:
        raise FocusedBehaviorGateError(f"{record.get('case_id')}: raw_response_path is missing")
    direct = extracted / raw_relative
    if direct.is_file():
        return direct
    case_id = record.get("case_id")
    candidates = sorted(extracted.rglob(f"{case_id}.txt")) if isinstance(case_id, str) else []
    if len(candidates) != 1:
        raise FocusedBehaviorGateError(f"{case_id}: cannot resolve raw response; candidates={[path.as_posix() for path in candidates]}")
    return candidates[0]


def _validate_span(case_id: str, observation: dict[str, Any], response_lines: list[str]) -> None:
    result = observation.get("result")
    start = observation.get("response_line_start")
    end = observation.get("response_line_end")
    excerpt = observation.get("evidence_excerpt")
    if result == "PASS":
        if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int):
            raise FocusedBehaviorGateError(f"{case_id}: PASS observation lacks integer line span")
        if start < 1 or end < start or end > len(response_lines):
            raise FocusedBehaviorGateError(f"{case_id}: PASS evidence span {start}-{end} is invalid")
        expected_excerpt = "\n".join(response_lines[start - 1 : end]).strip()
        if not expected_excerpt or excerpt != expected_excerpt:
            raise FocusedBehaviorGateError(f"{case_id}: PASS evidence excerpt does not match raw response")
    elif result == "ABSENT":
        if start is not None or end is not None or excerpt not in {"", None}:
            raise FocusedBehaviorGateError(f"{case_id}: ABSENT observation must not claim evidence")
    else:
        raise FocusedBehaviorGateError(f"{case_id}: focused gate requires PASS/ABSENT, got {result!r}")


def validate_focused_report(extracted: Path, report: dict[str, Any], expected_case_ids: list[str]) -> dict[str, Any]:
    expected = sorted(set(expected_case_ids))
    if len(expected) != len(expected_case_ids) or not expected:
        raise FocusedBehaviorGateError("expected focused case IDs must be a non-empty unique list")
    records = report.get("cases")
    if not isinstance(records, list):
        raise FocusedBehaviorGateError("focused report cases must be an array")
    actual_ids = sorted(record.get("case_id") for record in records if isinstance(record, dict))
    if actual_ids != expected:
        raise FocusedBehaviorGateError(f"focused case set mismatch; expected={expected}, actual={actual_ids}")
    if report.get("case_count") != len(expected):
        raise FocusedBehaviorGateError("focused report case_count is incorrect")
    if report.get("passed") != len(expected) or report.get("failed") != 0 or report.get("errored") != 0:
        raise FocusedBehaviorGateError(f"focused report did not pass all cases: passed={report.get('passed')} failed={report.get('failed')} errored={report.get('errored')}")
    if report.get("status") not in {"INCOMPLETE", "PASS"}:
        raise FocusedBehaviorGateError(f"focused report status is not promotable: {report.get('status')!r}")

    summaries: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise FocusedBehaviorGateError("focused case record must be an object")
        case_id = record.get("case_id")
        if record.get("result") != "PASS":
            raise FocusedBehaviorGateError(f"{case_id}: result must be PASS")
        if record.get("selected_skill") != record.get("expected_skill"):
            raise FocusedBehaviorGateError(f"{case_id}: selected skill does not match expected skill")
        raw_path = _resolve_raw_response(extracted, record)
        raw_sha = record.get("raw_response_sha256")
        if not isinstance(raw_sha, str) or not SHA256_RE.fullmatch(raw_sha) or _sha256(raw_path) != raw_sha:
            raise FocusedBehaviorGateError(f"{case_id}: raw response SHA-256 mismatch")
        lines = raw_path.read_text(encoding="utf-8").splitlines() or [""]
        required = record.get("required_observations")
        prohibited = record.get("prohibited_observations")
        if not isinstance(required, list) or not required or not isinstance(prohibited, list) or not prohibited:
            raise FocusedBehaviorGateError(f"{case_id}: observation arrays are incomplete")
        for observation in required:
            if not isinstance(observation, dict) or observation.get("result") != "PASS":
                raise FocusedBehaviorGateError(f"{case_id}: every required observation must PASS")
            _validate_span(str(case_id), observation, lines)
        for observation in prohibited:
            if not isinstance(observation, dict) or observation.get("result") != "ABSENT":
                raise FocusedBehaviorGateError(f"{case_id}: every prohibited observation must be ABSENT")
            _validate_span(str(case_id), observation, lines)
        summaries.append({"case_id": case_id, "selected_skill": record.get("selected_skill"), "raw_response_sha256": raw_sha, "required_count": len(required), "prohibited_count": len(prohibited), "result": "PASS"})

    return {"schema_version": "1.0.0", "status": "PASS", "focused_case_count": len(expected), "focused_case_ids": expected, "source_run_id": None, "source_commit_sha": report.get("commit_sha"), "package_payload_sha256": report.get("package_payload_sha256"), "catalog_sha256": report.get("catalog_sha256"), "harness_version": report.get("harness_version"), "cases": sorted(summaries, key=lambda item: str(item["case_id"])), "recommended_next_action": "Run the complete 34-case catalog without a case filter."}


def validate_run(repository: str, run_id: int, token: str, expected_case_ids: list[str], output: Path) -> dict[str, Any]:
    run = _request_json(f"https://api.github.com/repos/{repository}/actions/runs/{run_id}", token)
    if run.get("status") != "completed":
        raise FocusedBehaviorGateError(f"focused run {run_id} is not completed")
    artifacts = _request_json(f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/artifacts", token)
    items = artifacts.get("artifacts")
    if not isinstance(items, list):
        raise FocusedBehaviorGateError("focused run artifacts response is invalid")
    candidates = [item for item in items if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"].startswith("behavior-runtime-") and item.get("expired") is not True]
    if not candidates:
        raise FocusedBehaviorGateError(f"focused run {run_id} has no current behavior-runtime artifact")
    artifact = sorted(candidates, key=lambda item: int(item.get("id", 0)))[-1]
    artifact_id = artifact.get("id")
    if not isinstance(artifact_id, int):
        raise FocusedBehaviorGateError("focused artifact ID is invalid")
    with tempfile.TemporaryDirectory(prefix="creator-focused-behavior-") as directory:
        temporary = Path(directory)
        archive = temporary / "artifact.zip"
        extracted = temporary / "extracted"
        extracted.mkdir()
        _download(f"https://api.github.com/repos/{repository}/actions/artifacts/{artifact_id}/zip", token, archive)
        _safe_extract(archive, extracted)
        report = _load_json(_find_report(extracted))
        summary = validate_focused_report(extracted, report, expected_case_ids)
    summary.update({"source_run_id": run_id, "source_run_conclusion": run.get("conclusion"), "source_run_url": run.get("html_url"), "artifact_id": artifact_id, "artifact_name": artifact.get("name"), "artifact_digest": artifact.get("digest")})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--case-id", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if not args.token:
            raise FocusedBehaviorGateError("GitHub token is required")
        summary = validate_run(args.repository, args.run_id, args.token, args.case_id, args.output)
    except (FocusedBehaviorGateError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Focused behavior gate failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
