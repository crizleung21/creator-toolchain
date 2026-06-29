#!/usr/bin/env python3
"""Synchronize authoritative repo-local skills into the plugin package."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / ".agents/skills"
DESTINATION_ROOT = ROOT / "plugin/creator-toolchain/skills"

SKILLS = (
    "creator-orchestrator",
    "creator-intake-planner",
    "creator-execution-cycle",
    "creator-workspace-manager",
    "creator-rule-router",
    "creator-skill-workbench",
    "creator-evidence-audit",
)

EXCLUDED_NAMES = {
    ".DS_Store",
    ".Spotlight-V100",
    ".cache",
    ".gitkeep",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".vscode",
    "Thumbs.db",
    "__pycache__",
    "desktop.ini",
}
EXCLUDED_SUFFIXES = {".7z", ".bz2", ".gz", ".pyc", ".rar", ".tar", ".tgz", ".xz", ".zip"}


class SyncError(ValueError):
    """Raised when skill synchronization would cross a safety boundary."""


def _is_excluded(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDED_NAMES) or path.suffix in EXCLUDED_SUFFIXES


def _validate_source(source_root: Path) -> None:
    if not source_root.is_dir():
        raise SyncError(f"source skill root does not exist: {source_root}")

    source_skills = {
        path.name
        for path in source_root.iterdir()
        if path.is_dir() and path.name not in EXCLUDED_NAMES
    }
    unknown = sorted(source_skills - set(SKILLS))
    if unknown:
        raise SyncError(f"unknown source skill: {', '.join(unknown)}")

    missing = sorted(set(SKILLS) - source_skills)
    if missing:
        raise SyncError(f"missing source skill: {', '.join(missing)}")

    resolved_root = source_root.resolve()
    for path in source_root.rglob("*"):
        if not path.is_symlink():
            continue
        resolved = path.resolve()
        try:
            resolved.relative_to(resolved_root)
        except ValueError as exc:
            raise SyncError(f"symlink escapes source root: {path}") from exc


def _files(root: Path, skill: str) -> dict[Path, bytes]:
    skill_root = root / skill
    if not skill_root.is_dir():
        return {}

    result: dict[Path, bytes] = {}
    for path in sorted(skill_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(skill_root)
        if _is_excluded(relative):
            continue
        result[relative] = path.read_bytes()
    return result


def _compare(source_root: Path, destination_root: Path) -> list[str]:
    findings: list[str] = []
    for skill in SKILLS:
        source_files = _files(source_root, skill)
        destination_files = _files(destination_root, skill)
        for relative in sorted(source_files.keys() - destination_files.keys()):
            findings.append(f"missing: {skill}/{relative.as_posix()}")
        for relative in sorted(destination_files.keys() - source_files.keys()):
            findings.append(f"extra: {skill}/{relative.as_posix()}")
        for relative in sorted(source_files.keys() & destination_files.keys()):
            if source_files[relative] != destination_files[relative]:
                findings.append(f"different: {skill}/{relative.as_posix()}")

    if destination_root.is_dir():
        destination_skills = {
            path.name
            for path in destination_root.iterdir()
            if path.is_dir() and path.name not in EXCLUDED_NAMES
        }
        for skill in sorted(destination_skills - set(SKILLS)):
            findings.append(f"extra-skill: {skill}")
    return findings


def synchronize(
    source_root: Path,
    destination_root: Path,
    *,
    write: bool,
) -> list[str]:
    """Write or compare the plugin mirror and return deterministic findings."""

    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    _validate_source(source_root)

    if write:
        if (
            source_root == destination_root
            or source_root.is_relative_to(destination_root)
            or destination_root.is_relative_to(source_root)
        ):
            raise SyncError("source and destination roots must not overlap")
        if destination_root.exists():
            if destination_root.is_symlink():
                raise SyncError(f"destination skill root must not be a symlink: {destination_root}")
            shutil.rmtree(destination_root)
        destination_root.mkdir(parents=True, exist_ok=True)
        ignore = shutil.ignore_patterns(
            *sorted(EXCLUDED_NAMES),
            *(f"*{suffix}" for suffix in sorted(EXCLUDED_SUFFIXES)),
        )
        for skill in SKILLS:
            destination = destination_root / skill
            shutil.copytree(source_root / skill, destination, ignore=ignore)

    return _compare(source_root, destination_root)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="replace the plugin skill mirror")
    mode.add_argument("--check", action="store_true", help="check mirror parity without writing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        findings = synchronize(SOURCE_ROOT, DESTINATION_ROOT, write=args.write)
    except SyncError as exc:
        print(f"Skill sync failed: {exc}", file=sys.stderr)
        return 1

    if findings:
        print("Plugin skill mirror differs from the authoritative source:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    action = "synchronized" if args.write else "matches"
    print(f"Plugin skill mirror {action} authoritative source ({len(SKILLS)} skills).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
