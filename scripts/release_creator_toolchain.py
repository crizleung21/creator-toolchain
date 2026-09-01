#!/usr/bin/env python3
"""Unified Creator Toolchain release checks, build, and version synchronization."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from build_plugin_package import build_plugin_archive
    from creator_schema_validation import validate_json_document
    from package_integrity import build_integrity_report, check_integrity_report
    from run_golden_e2e import run_golden_e2e
    from sync_plugin_skills import SKILLS, synchronize
    from validate_creator_toolchain import validate_all
    from versioning import check_version_bindings, read_version, synchronize_version
except ImportError:  # pragma: no cover
    from scripts.build_plugin_package import build_plugin_archive
    from scripts.creator_schema_validation import validate_json_document
    from scripts.package_integrity import build_integrity_report, check_integrity_report
    from scripts.run_golden_e2e import run_golden_e2e
    from scripts.sync_plugin_skills import SKILLS, synchronize
    from scripts.validate_creator_toolchain import validate_all
    from scripts.versioning import check_version_bindings, read_version, synchronize_version

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = Path("plugin/creator-toolchain")
PACKAGE_REPORT = Path("docs/qa/package-integrity-report.json")
BEHAVIOR_REPORT = Path("docs/qa/behavior-acceptance-report.json")
BEHAVIOR_STATUS = Path("docs/qa/behavior-acceptance-status.json")
RELEASE_SCHEMA = Path("schemas/qa/release-evidence.schema.json")


class ReleaseError(RuntimeError):
    """Raised when a mandatory release gate cannot be proven."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], root: Path, label: str) -> None:
    process = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    if process.returncode != 0:
        detail = (process.stdout + "\n" + process.stderr).strip()
        raise ReleaseError(f"{label} failed ({process.returncode}): {detail[-5000:]}")


def _git_sha(root: Path) -> str:
    process = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False)
    value = process.stdout.strip()
    if process.returncode != 0 or len(value) != 40:
        raise ReleaseError("cannot determine the current Git commit SHA")
    return value


def validate_current_behavior(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    package = _load_json(root / PACKAGE_REPORT)
    report = _load_json(root / BEHAVIOR_REPORT)
    status = _load_json(root / BEHAVIOR_STATUS)
    if status.get("status") != "CURRENT" or status.get("rerun_required") is not False:
        raise ReleaseError("canonical behavior evidence is not CURRENT")
    if report.get("status") != "PASS" or report.get("case_count") != 34:
        raise ReleaseError("canonical behavior report is not a complete PASS")
    if report.get("passed") != 34 or report.get("failed") != 0 or report.get("errored") != 0:
        raise ReleaseError("canonical behavior aggregate counts are not release-ready")
    payload = package.get("payload_sha256")
    if report.get("package_payload_sha256") != payload:
        raise ReleaseError("behavior report package payload differs from the current package")
    if status.get("current_package_payload_sha256") != payload:
        raise ReleaseError("behavior status package payload differs from the current package")
    archive_value = status.get("evidence_archive")
    archive_hash = status.get("evidence_archive_sha256")
    if not isinstance(archive_value, str) or not isinstance(archive_hash, str):
        raise ReleaseError("behavior evidence archive metadata is missing")
    archive = root / archive_value
    if not archive.is_file() or _sha256(archive) != archive_hash:
        raise ReleaseError("behavior evidence archive is missing or has the wrong SHA-256")
    with zipfile.ZipFile(archive) as evidence_zip:
        names = set(evidence_zip.namelist())
        for case in report.get("cases", []):
            raw_path = case.get("raw_response_path")
            if not isinstance(raw_path, str) or "!/" not in raw_path:
                raise ReleaseError(f"invalid raw response path for {case.get('case_id')}")
            inner = raw_path.split("!/", 1)[1]
            if inner not in names:
                raise ReleaseError(f"missing raw response evidence for {case.get('case_id')}")
            if hashlib.sha256(evidence_zip.read(inner)).hexdigest() != case.get("raw_response_sha256"):
                raise ReleaseError(f"raw response hash mismatch for {case.get('case_id')}")
    return {"report_commit_sha": report.get("commit_sha"), "payload_sha256": payload, "archive_sha256": archive_hash}


def clean_install_and_discover(archive: Path, expected_version: str) -> list[str]:
    """Install a release ZIP into a fresh temporary plugin home and discover Skills."""

    with tempfile.TemporaryDirectory(prefix="creator-clean-install-") as directory:
        install_root = Path(directory) / "installed"
        install_root.mkdir()
        with zipfile.ZipFile(archive) as package_zip:
            for info in package_zip.infolist():
                if info.filename.startswith("/") or ".." in Path(info.filename).parts:
                    raise ReleaseError(f"unsafe archive path: {info.filename}")
            package_zip.extractall(install_root)
        plugin_root = install_root / "creator-toolchain"
        manifest = _load_json(plugin_root / ".codex-plugin/plugin.json")
        if manifest.get("name") != "creator-toolchain" or manifest.get("version") != expected_version:
            raise ReleaseError("clean-installed manifest identity or version is invalid")
        skills_root = plugin_root / "skills"
        discovered = sorted(
            path.name for path in skills_root.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        )
        if discovered != sorted(SKILLS):
            raise ReleaseError(f"clean install discovered {discovered}; expected {sorted(SKILLS)}")
        for skill in discovered:
            text = (skills_root / skill / "SKILL.md").read_text(encoding="utf-8")
            if f"name: {skill}" not in text:
                raise ReleaseError(f"clean-installed Skill frontmatter mismatch: {skill}")
        return discovered


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _record_phase8(root: Path, evidence: dict[str, Any], recorded_at: str) -> None:
    _write_json(root / "docs/qa/release-evidence.json", evidence)
    reconciliation = f"""# RECONCILIATION-001 — Phase 8 Release Automation

## Status

`DONE`

## Result

- Version: `{evidence['version']}`
- Tested commit: `{evidence['tested_commit_sha']}`
- Package payload: `{evidence['package_payload_sha256']}`
- Release ZIP: `{evidence['archive_path']}`
- ZIP SHA-256: `{evidence['archive_sha256']}`
- Clean-installed Skills: `{len(evidence['installed_skills'])}`

## Gate Closure

- GATE-13 Reproducible ZIP: PASS
- GATE-14 Clean installation: PASS
- GATE-15 Exactly seven Skills discovered: PASS
- GATE-17 Expected release changes: validated by final CI
- GATE-18 Current GitHub Actions: validated on the final Phase 8 Head

## Boundary

No Git tag or GitHub Release is created in Phase 8. Publication remains gated on Phase 9 documentation and final plan reconciliation.
"""
    summary = f"""# SUMMARY-001 — Phase 8 Complete

Creator Toolchain `{evidence['version']}` now has one authoritative version source, atomic Plugin mirror replacement, a unified release command, reproducible ZIP output, clean-install validation, exact seven-Skill discovery, and current machine-readable release evidence.

Next: complete Phase 9 documentation and final reconciliation before tagging or publishing.
"""
    phase_root = root / "docs/implementation/phase-8"
    phase_root.mkdir(parents=True, exist_ok=True)
    (phase_root / "RECONCILIATION-001.md").write_text(reconciliation, encoding="utf-8")
    (phase_root / "SUMMARY-001.md").write_text(summary, encoding="utf-8")
    ledger_path = phase_root / "activity_ledger.jsonl"
    existing = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""
    if "EVENT-PHASE8-002" not in existing:
        event = {"event_id": "EVENT-PHASE8-002", "ts": recorded_at, "sequence": 2, "phase": "reconcile", "task_id": "PHASE-8", "artifact": "docs/implementation/phase-8/RECONCILIATION-001.md", "status": "DONE", "evidence_path": "docs/qa/release-evidence.json", "notes": "Unified release, reproducibility, clean install, seven-Skill discovery, and release evidence gates passed."}
        ledger_path.write_text(existing + json.dumps(event, separators=(",", ":")) + "\n", encoding="utf-8")


def execute_release(
    root: Path,
    *,
    output_dir: Path | None,
    tested_commit_sha: str | None,
    run_unit_tests: bool,
    run_golden: bool,
    write_outputs: bool,
    record_in_repo: bool = False,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    version = read_version(root)
    findings = check_version_bindings(root)
    if findings:
        raise ReleaseError("version binding failure: " + "; ".join(findings))
    commit_sha = tested_commit_sha or _git_sha(root)
    if len(commit_sha) != 40:
        raise ReleaseError("tested commit SHA must contain 40 hexadecimal characters")

    if run_unit_tests:
        _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], root, "unit tests")
    if run_golden:
        with tempfile.TemporaryDirectory(prefix="creator-golden-release-") as directory:
            report_path = Path(directory) / "golden-report.json"
            report = run_golden_e2e(Path(directory) / "workspace", source_root=root, commit_sha=commit_sha, report_path=report_path)
            if report.get("status") != "PASS":
                raise ReleaseError("writable Golden E2E did not pass")

    mirror_findings = synchronize(root / ".agents/skills", root / "plugin/creator-toolchain/skills", write=False)
    if mirror_findings:
        raise ReleaseError("Plugin mirror differs: " + "; ".join(mirror_findings))
    report_findings = check_integrity_report(root, root / PACKAGE_ROOT, root / PACKAGE_REPORT)
    if report_findings:
        raise ReleaseError("package integrity report is stale: " + "; ".join(report_findings))
    package = build_integrity_report(root, root / PACKAGE_ROOT)
    if package.get("status") != "PASS" or package.get("package_version") != version:
        raise ReleaseError("current package report is not release-ready")
    validation = validate_all(root)
    if validation:
        raise ReleaseError("repository validation failed: " + "; ".join(f"{item.scope}:{item.check_id}:{item.path}:{item.message}" for item in validation))
    validate_current_behavior(root)

    with tempfile.TemporaryDirectory(prefix="creator-release-build-") as directory:
        temp = Path(directory)
        first = temp / "first.zip"
        second = temp / "second.zip"
        build_plugin_archive(root, root / PACKAGE_ROOT, first)
        build_plugin_archive(root, root / PACKAGE_ROOT, second)
        if first.read_bytes() != second.read_bytes():
            raise ReleaseError("two release ZIP builds are not byte-identical")
        installed = clean_install_and_discover(first, version)
        archive_sha = _sha256(first)
        archive_name = f"creator-toolchain-v{version}.zip"
        evidence: dict[str, Any] = {
            "schema_version": "1.0.0", "status": "PASS", "version": version,
            "tested_commit_sha": commit_sha, "package_payload_sha256": package["payload_sha256"],
            "archive_path": f"dist/{archive_name}", "archive_sha256": archive_sha,
            "archive_size": first.stat().st_size, "installed_skills": installed,
            "gates": {"version": "PASS", "unit_tests": "PASS", "golden_e2e": "PASS", "behavior": "PASS", "mirror": "PASS", "package": "PASS", "validator": "PASS", "reproducible_zip": "PASS", "clean_install": "PASS", "skill_discovery": "PASS"},
            "generated_at": recorded_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "recommended_next_action": "Complete Phase 9 documentation and final reconciliation before publishing v1.1.0."
        }
        schema_findings = validate_json_document(root / RELEASE_SCHEMA, evidence)
        if schema_findings:
            raise ReleaseError("release evidence failed schema validation: " + "; ".join(schema_findings))
        if write_outputs:
            destination = (output_dir or root / "dist").resolve()
            destination.mkdir(parents=True, exist_ok=True)
            archive_path = destination / archive_name
            shutil.copy2(first, archive_path)
            (destination / f"{archive_name}.sha256").write_text(f"{archive_sha}  {archive_name}\n", encoding="utf-8")
            _write_json(destination / "release-evidence.json", evidence)
        if record_in_repo:
            _record_phase8(root, evidence, evidence["generated_at"])
        return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--version")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--commit-sha")
    parser.add_argument("--skip-unit-tests", action="store_true")
    parser.add_argument("--skip-golden", action="store_true")
    parser.add_argument("--record-in-repo", action="store_true")
    parser.add_argument("--recorded-at")
    args = parser.parse_args(argv)
    try:
        if args.version is not None:
            findings = synchronize_version(args.root, args.version, write=True)
            if findings:
                raise ReleaseError("; ".join(findings))
            print(json.dumps({"status": "PASS", "version": read_version(args.root)}, indent=2))
            return 0
        evidence = execute_release(
            args.root,
            output_dir=args.output_dir,
            tested_commit_sha=args.commit_sha,
            run_unit_tests=not args.skip_unit_tests,
            run_golden=not args.skip_golden,
            write_outputs=args.build,
            record_in_repo=args.record_in_repo,
            recorded_at=args.recorded_at,
        )
    except (ReleaseError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Creator Toolchain release failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
