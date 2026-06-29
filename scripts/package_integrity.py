#!/usr/bin/env python3
"""Build and verify the deterministic Creator Toolchain package inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from sync_plugin_skills import (
        EXCLUDED_NAMES,
        EXCLUDED_SUFFIXES,
        SKILLS,
        SyncError,
        synchronize,
    )
except ImportError:  # Imported as scripts.package_integrity in tests.
    from scripts.sync_plugin_skills import (
        EXCLUDED_NAMES,
        EXCLUDED_SUFFIXES,
        SKILLS,
        SyncError,
        synchronize,
    )


SCHEMA_VERSION = "1.0.0"
PACKAGE_RELATIVE = Path("plugin/creator-toolchain")
REQUIRED_PACKAGE_FILES = {
    Path(".codex-plugin/plugin.json"),
    Path("CHANGELOG.md"),
    Path("LICENSE"),
    Path("README.md"),
}
FORBIDDEN_PARTS = {
    ".agents",
    ".cache",
    ".creator",
    ".idea",
    ".git",
    ".DS_Store",
    ".Spotlight-V100",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".vscode",
    "Thumbs.db",
    "__pycache__",
    "desktop.ini",
    "package",
    "private",
}
FORBIDDEN_SUFFIXES = {".7z", ".bz2", ".gz", ".pyc", ".rar", ".tar", ".tgz", ".xz", ".zip"}


class PackageIntegrityError(RuntimeError):
    """Raised when a package cannot be enumerated safely."""


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_source_excluded(relative: Path) -> bool:
    return any(part in EXCLUDED_NAMES for part in relative.parts) or any(
        relative.name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES
    )


def _expected_package_files(root: Path) -> set[Path]:
    expected = set(REQUIRED_PACKAGE_FILES)
    source_root = root / ".agents/skills"
    for skill in SKILLS:
        skill_root = source_root / skill
        if not skill_root.is_dir():
            continue
        for path in sorted(skill_root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(skill_root)
            if not _is_source_excluded(relative):
                expected.add(Path("skills") / skill / relative)
    return expected


def _forbidden(relative: Path) -> bool:
    return (
        bool(set(relative.parts) & FORBIDDEN_PARTS)
        or relative.name.startswith(".env")
        or relative.name.endswith(".local.json")
        or relative.suffix in FORBIDDEN_SUFFIXES
    )


def _finding(check_id: str, path: Path | str, message: str) -> dict[str, str]:
    return {"check_id": check_id, "path": str(path), "message": message}


def _collect(
    root: Path,
    package_root: Path,
) -> tuple[list[Path], list[dict[str, str]], str, str]:
    root = root.resolve()
    package_root = package_root.resolve()
    findings: list[dict[str, str]] = []
    expected = _expected_package_files(root)

    if not package_root.is_dir():
        return [], [_finding("PACKAGE_ROOT", package_root, "package root is missing")], "FAIL", ""

    actual_files: set[Path] = set()
    for path in sorted(package_root.rglob("*")):
        relative = path.relative_to(package_root)
        if path.is_symlink():
            findings.append(_finding("SYMLINK", relative, "symbolic links are prohibited"))
            continue
        if path.is_dir():
            if _forbidden(relative):
                findings.append(_finding("FORBIDDEN_PATH", relative, "forbidden package path"))
            continue
        if not path.is_file():
            findings.append(_finding("NON_REGULAR_FILE", relative, "non-regular package entry"))
            continue
        actual_files.add(relative)
        if _forbidden(relative):
            findings.append(_finding("FORBIDDEN_PATH", relative, "forbidden package path"))
        elif relative not in expected:
            findings.append(_finding("UNEXPECTED_PATH", relative, "path is not in the package allowlist"))

    for relative in sorted(expected - actual_files):
        findings.append(_finding("MISSING_REQUIRED", relative, "required package file is missing"))

    mirror_status = "PASS"
    try:
        parity = synchronize(root / ".agents/skills", package_root / "skills", write=False)
    except SyncError as exc:
        parity = [str(exc)]
    if parity:
        mirror_status = "FAIL"
        findings.extend(_finding("MIRROR_PARITY", "skills", message) for message in parity)

    version = ""
    manifest_path = package_root / ".codex-plugin/plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(_finding("MANIFEST", ".codex-plugin/plugin.json", f"invalid manifest: {exc}"))
    else:
        value = manifest.get("version") if isinstance(manifest, dict) else None
        if isinstance(value, str):
            version = value
        else:
            findings.append(_finding("MANIFEST", ".codex-plugin/plugin.json", "version is missing"))

    files = [package_root / relative for relative in sorted(actual_files & expected)]
    unique_findings = {
        (item["check_id"], item["path"], item["message"]): item for item in findings
    }
    ordered_findings = [unique_findings[key] for key in sorted(unique_findings)]
    return files, ordered_findings, mirror_status, version


def enumerate_package_files(root: Path, package_root: Path) -> list[Path]:
    files, findings, _, _ = _collect(root, package_root)
    if findings:
        details = "; ".join(
            f"{item['check_id']}:{item['path']}:{item['message']}" for item in findings
        )
        raise PackageIntegrityError(details)
    return files


def payload_sha256(files: list[Path], package_root: Path) -> str:
    package_root = package_root.resolve()
    digest = hashlib.sha256()
    resolved_files = [path.resolve() for path in files]
    for resolved in sorted(
        resolved_files,
        key=lambda item: item.relative_to(package_root).as_posix(),
    ):
        try:
            relative = resolved.relative_to(package_root)
        except ValueError as exc:
            raise PackageIntegrityError(f"payload file escapes package root: {resolved}") from exc
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(resolved.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_integrity_report(root: Path, package_root: Path) -> dict[str, object]:
    root = root.resolve()
    package_root = package_root.resolve()
    files, findings, mirror_status, version = _collect(root, package_root)
    try:
        package_relative = package_root.relative_to(root).as_posix()
    except ValueError:
        package_relative = package_root.as_posix()
    records = [
        {
            "path": path.relative_to(package_root).as_posix(),
            "sha256": file_sha256(path),
        }
        for path in files
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not findings else "FAIL",
        "package_version": version,
        "package_root": package_relative,
        "file_count": len(records),
        "payload_sha256": payload_sha256(files, package_root),
        "files": records,
        "mirror_status": mirror_status,
        "findings": findings,
    }


def check_integrity_report(
    root: Path,
    package_root: Path,
    report_path: Path,
) -> list[str]:
    current = build_integrity_report(root, package_root)
    try:
        recorded: Any = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read integrity report: {exc}"]
    findings: list[str] = []
    if current.get("status") != "PASS":
        findings.append("current package integrity status is not PASS")
    if recorded != current:
        findings.append("stale integrity report: current package differs from recorded report")
    return findings


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--package-root", type=Path, default=PACKAGE_RELATIVE)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", type=Path)
    mode.add_argument("--check", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = args.root.resolve()
    package_root = args.package_root
    if not package_root.is_absolute():
        package_root = root / package_root
    report = build_integrity_report(root, package_root)
    if args.write:
        report_path = args.write if args.write.is_absolute() else root / args.write
        _write_report(report_path, report)
    elif args.check:
        report_path = args.check if args.check.is_absolute() else root / args.check
        findings = check_integrity_report(root, package_root, report_path)
        if findings:
            for finding in findings:
                print(f"FAIL: {finding}", file=sys.stderr)
            return 1
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
