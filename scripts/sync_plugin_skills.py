#!/usr/bin/env python3
"""Atomically synchronize authoritative repo-local skills into the Plugin mirror."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable

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
    ".DS_Store", ".Spotlight-V100", ".cache", ".gitkeep", ".idea",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".vscode",
    "Thumbs.db", "__pycache__", "desktop.ini",
}
EXCLUDED_SUFFIXES = {".7z", ".bz2", ".gz", ".pyc", ".rar", ".tar", ".tgz", ".xz", ".zip"}


class SyncError(ValueError):
    """Raised when synchronization would violate a safety or parity invariant."""


def _is_excluded(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDED_NAMES) or path.suffix in EXCLUDED_SUFFIXES


def _reject_symlinks(root: Path, label: str) -> None:
    if root.is_symlink():
        raise SyncError(f"{label} root must not be a symlink: {root}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SyncError(f"{label} contains a symlink: {path}")


def _validate_source(source_root: Path) -> None:
    if not source_root.is_dir():
        raise SyncError(f"source skill root does not exist: {source_root}")
    _reject_symlinks(source_root, "source")
    source_skills = {
        path.name for path in source_root.iterdir()
        if path.is_dir() and path.name not in EXCLUDED_NAMES
    }
    unknown = sorted(source_skills - set(SKILLS))
    missing = sorted(set(SKILLS) - source_skills)
    if unknown:
        raise SyncError(f"unknown source skill: {', '.join(unknown)}")
    if missing:
        raise SyncError(f"missing source skill: {', '.join(missing)}")


def _validate_roots(source_root: Path, destination_root: Path) -> None:
    if (
        source_root == destination_root
        or source_root.is_relative_to(destination_root)
        or destination_root.is_relative_to(source_root)
    ):
        raise SyncError("source and destination roots must not overlap")
    if destination_root.exists() and destination_root.is_symlink():
        raise SyncError(f"destination skill root must not be a symlink: {destination_root}")


def _files(root: Path, skill: str) -> dict[Path, bytes]:
    skill_root = root / skill
    if not skill_root.is_dir():
        return {}
    result: dict[Path, bytes] = {}
    for path in sorted(skill_root.rglob("*")):
        if path.is_symlink():
            raise SyncError(f"skill mirror contains a symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(skill_root)
        if not _is_excluded(relative):
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
            path.name for path in destination_root.iterdir()
            if path.is_dir() and path.name not in EXCLUDED_NAMES
        }
        findings.extend(
            f"extra-skill: {skill}" for skill in sorted(destination_skills - set(SKILLS))
        )
    return findings


def _copy_to_stage(source_root: Path, stage: Path) -> None:
    stage.mkdir(parents=True, exist_ok=False)
    for skill in SKILLS:
        source_skill = source_root / skill
        destination_skill = stage / skill
        destination_skill.mkdir()
        for source in sorted(source_skill.rglob("*")):
            relative = source.relative_to(source_skill)
            if _is_excluded(relative):
                continue
            if source.is_symlink():
                raise SyncError(f"source contains a symlink: {source}")
            target = destination_skill / relative
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)


def synchronize(
    source_root: Path,
    destination_root: Path,
    *,
    write: bool,
    failure_injector: Callable[[str], None] | None = None,
) -> list[str]:
    """Compare or atomically replace the Plugin mirror.

    The old mirror remains available as a sibling backup until the staged mirror
    has been installed and parity-checked. Any exception restores the old bytes.
    """

    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    _validate_source(source_root)
    _validate_roots(source_root, destination_root)
    if not write:
        return _compare(source_root, destination_root)

    destination_root.parent.mkdir(parents=True, exist_ok=True)
    temporary_parent = Path(tempfile.mkdtemp(prefix=f".{destination_root.name}.sync-", dir=destination_root.parent))
    stage = temporary_parent / "staged"
    backup = temporary_parent / "backup"
    old_existed = destination_root.exists()
    installed = False
    try:
        _copy_to_stage(source_root, stage)
        staged_findings = _compare(source_root, stage)
        if staged_findings:
            raise SyncError("staged mirror failed parity: " + "; ".join(staged_findings))
        if old_existed:
            os.replace(destination_root, backup)
        if failure_injector is not None:
            failure_injector("after_backup")
        os.replace(stage, destination_root)
        installed = True
        if failure_injector is not None:
            failure_injector("after_install")
        findings = _compare(source_root, destination_root)
        if findings:
            raise SyncError("installed mirror failed parity: " + "; ".join(findings))
        if backup.exists():
            shutil.rmtree(backup)
        return []
    except Exception as exc:
        try:
            if installed and destination_root.exists():
                shutil.rmtree(destination_root)
            if old_existed and backup.exists():
                os.replace(backup, destination_root)
        except Exception as rollback_exc:  # pragma: no cover
            raise SyncError(f"synchronization failed and rollback failed: {rollback_exc}") from exc
        if isinstance(exc, SyncError):
            raise
        raise SyncError(str(exc)) from exc
    finally:
        shutil.rmtree(temporary_parent, ignore_errors=True)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
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
    raise SystemExit(main())
