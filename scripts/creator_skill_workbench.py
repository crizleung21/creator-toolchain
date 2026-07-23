#!/usr/bin/env python3
"""Deterministically score Creator Toolchain skills with evidence-backed deductions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from json_schema_lite import load_schema, validate as validate_json_schema
except ImportError:
    from scripts.json_schema_lite import load_schema, validate as validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
CONFIG_RELATIVE = Path("config/skill-workbench-score.json")
SCHEMA_RELATIVE = Path("schemas/skill-workbench/score-report.schema.json")
RESOURCE_RE = re.compile(r"`((?:references|assets)/[A-Za-z0-9_./-]+)`")


class SkillWorkbenchError(RuntimeError):
    """Raised when a skill cannot be scored deterministically."""


def _parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}
    try:
        closing = lines.index("---", 1)
    except ValueError:
        return {}
    values: dict[str, str] = {}
    for line in lines[1:closing]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def load_score_config(root: Path = ROOT) -> dict[str, Any]:
    path = Path(root) / CONFIG_RELATIVE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SkillWorkbenchError(f"cannot load score config: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "1.0.0":
        raise SkillWorkbenchError("score config schema_version must be 1.0.0")
    dimensions = value.get("dimensions")
    thresholds = value.get("thresholds")
    if not isinstance(dimensions, list) or not isinstance(thresholds, list):
        raise SkillWorkbenchError("score config dimensions and thresholds must be arrays")
    names = [item.get("dimension") for item in dimensions if isinstance(item, dict)]
    weights = [item.get("weight") for item in dimensions if isinstance(item, dict)]
    if len(names) != len(set(names)) or not all(isinstance(item, int) and item >= 0 for item in weights) or sum(weights) != 100:
        raise SkillWorkbenchError("score dimensions must be unique non-negative weights totaling 100")
    minimums = [item.get("minimum") for item in thresholds if isinstance(item, dict)]
    if not all(isinstance(item, int) for item in minimums) or sorted(minimums, reverse=True) != minimums:
        raise SkillWorkbenchError("score thresholds must be ordered by descending minimum")
    return value


def _safe_skill_path(root: Path, skill_relative: str | Path) -> Path:
    root = Path(root).resolve()
    relative = Path(skill_relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise SkillWorkbenchError(f"unsafe skill path: {skill_relative}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SkillWorkbenchError(f"skill path escapes repository: {skill_relative}") from exc
    if not path.is_dir() or not (path / "SKILL.md").is_file():
        raise SkillWorkbenchError(f"skill directory or SKILL.md is missing: {skill_relative}")
    return path


def _duplicate_count(skill_root: Path, skill_name: str) -> int:
    count = 0
    if not skill_root.is_dir():
        return count
    for skill_file in sorted(skill_root.glob("*/SKILL.md")):
        try:
            values = _parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        except OSError:
            continue
        if values.get("name") == skill_name:
            count += 1
    return count


def _tests_mention(root: Path, skill_name: str) -> bool:
    tests_root = root / "tests"
    if not tests_root.is_dir():
        return False
    for path in sorted(tests_root.rglob("test_*.py")):
        try:
            if skill_name in path.read_text(encoding="utf-8"):
                return True
        except OSError:
            continue
    return False


def _check(points: int, passed: bool, check_id: str, evidence: str) -> tuple[int, bool, str, str]:
    return points, passed, check_id, evidence


def score_skill(root: Path, skill_relative: str | Path, *, schema_root: Path = ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    schema_root = Path(schema_root).resolve()
    skill_path = _safe_skill_path(root, skill_relative)
    skill_file = skill_path / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    lower = text.casefold()
    frontmatter = _parse_frontmatter(text)
    skill_name = frontmatter.get("name") or skill_path.name
    description = frontmatter.get("description", "")
    resources = sorted(set(RESOURCE_RE.findall(text)))
    missing_resources = [item for item in resources if not (skill_path / item).is_file()]
    bullet_count = sum(line.lstrip().startswith("- ") for line in text.splitlines())
    skill_root = root / ".agents/skills"
    duplicate_count = _duplicate_count(skill_root, skill_name)
    has_tests = _tests_mention(root, skill_name)

    checks: dict[str, list[tuple[int, bool, str, str]]] = {
        "trigger_precision": [
            _check(5, len(description) >= 40, "TRIGGER_DESCRIPTION", f"description length={len(description)}"),
            _check(5, any(token in description.casefold() for token in ("route", "convert", "execute", "manage", "select", "discover", "audit", "build", "create", "inspect", "maintain")), "TRIGGER_ACTION", f"description={description!r}"),
            _check(5, any(token in description.casefold() for token in ("use when", "use for", "including", "across", "workflow", "project", "skill", "rule", "state", "audit")), "TRIGGER_SCOPE", f"description={description!r}"),
        ],
        "boundary_clarity": [
            _check(8, "## guardrails" in lower or "## boundaries" in lower or "## boundary" in lower, "BOUNDARY_SECTION", "Guardrails or boundary heading"),
            _check(7, any(token in lower for token in ("do not", "must not", "never ", "not for")), "BOUNDARY_LANGUAGE", "Explicit negative boundary language"),
        ],
        "workflow_completeness": [
            _check(8, any(token in lower for token in ("## workflows", "## modes", "## operations", "## routing matrix")), "WORKFLOW_ENTRY", "Workflow, mode, operation, or routing section"),
            _check(6, any(token in lower for token in ("## output contract", "## required output", "## required checks", "## output model")), "WORKFLOW_OUTPUT", "Output or required-check contract"),
            _check(6, bullet_count >= 3, "WORKFLOW_STEPS", f"bullet_count={bullet_count}"),
        ],
        "progressive_disclosure": [
            _check(5, "references/" in text, "DISCLOSURE_REFERENCES", "SKILL.md points to references"),
            _check(5, "assets/" in text, "DISCLOSURE_ASSETS", "SKILL.md points to assets"),
            _check(5, len(text.splitlines()) <= 250 and bool(resources), "DISCLOSURE_ENTRY_SIZE", f"line_count={len(text.splitlines())}, resource_count={len(resources)}"),
        ],
        "state_safety": [
            _check(5, ".creator/" in text or "state surface" in lower or "state surfaces" in lower, "STATE_SURFACE", "State surface is named"),
            _check(5, "mutat" in lower and any(token in lower for token in ("do not", "atomic", "read", "write", "owner")), "STATE_MUTATION", "State mutation boundary is explicit"),
        ],
        "reference_integrity": [
            _check(5, bool(resources), "REFERENCE_DECLARED", f"resource_count={len(resources)}"),
            _check(5, bool(resources) and not missing_resources, "REFERENCE_EXISTS", f"missing_resources={missing_resources}"),
        ],
        "acceptance_tests": [
            _check(5, any(token in lower for token in ("acceptance test", "acceptance criteria", "verification", "required checks", "qa gate")), "ACCEPTANCE_CONTRACT", "Acceptance or verification language"),
            _check(5, has_tests, "ACCEPTANCE_TEST_FILE", f"tests mention {skill_name}={has_tests}"),
        ],
        "naming_collision": [
            _check(3, skill_name == skill_path.name, "NAME_DIRECTORY", f"frontmatter={skill_name!r}, directory={skill_path.name!r}"),
            _check(2, duplicate_count == 1, "NAME_UNIQUE", f"duplicate_count={duplicate_count}"),
        ],
    }

    config = load_score_config(schema_root)
    weights = {item["dimension"]: item["weight"] for item in config["dimensions"]}
    dimensions: list[dict[str, Any]] = []
    deductions: list[dict[str, Any]] = []
    score = 0
    for dimension in [item["dimension"] for item in config["dimensions"]]:
        dimension_checks = checks.get(dimension, [])
        awarded = sum(points for points, passed, _, _ in dimension_checks if passed)
        if awarded > weights[dimension]:
            raise SkillWorkbenchError(f"dimension awarded points exceed weight: {dimension}")
        findings: list[str] = []
        for points, passed, check_id, evidence in dimension_checks:
            findings.append(f"{'PASS' if passed else 'FAIL'} {check_id}: {evidence}")
            if not passed:
                deductions.append({"dimension": dimension, "points": points, "check_id": check_id, "evidence": evidence})
        dimensions.append({"dimension": dimension, "weight": weights[dimension], "awarded": awarded, "findings": findings})
        score += awarded
    status = next(item["status"] for item in config["thresholds"] if score >= item["minimum"])
    next_action = "No remediation is required before packaging." if not deductions else f"Address {deductions[0]['check_id']} first, then rerun the score."
    report = {
        "schema_version": "1.0.0",
        "skill_name": skill_name,
        "skill_path": skill_path.relative_to(root).as_posix(),
        "score": score,
        "status": status,
        "dimensions": dimensions,
        "deductions": deductions,
        "summary": f"{skill_name} scored {score}/100 with {len(deductions)} evidence-backed deduction(s).",
        "recommended_next_action": next_action,
    }
    findings = validate_json_schema(report, load_schema(schema_root / SCHEMA_RELATIVE))
    if findings:
        raise SkillWorkbenchError("score report failed schema validation: " + "; ".join(findings))
    return report


def score_all(root: Path, *, schema_root: Path = ROOT) -> list[dict[str, Any]]:
    root = Path(root).resolve()
    skill_root = root / ".agents/skills"
    if not skill_root.is_dir():
        raise SkillWorkbenchError(".agents/skills is missing")
    return [score_skill(root, path.relative_to(root), schema_root=schema_root) for path in sorted(skill_root.iterdir()) if path.is_dir() and (path / "SKILL.md").is_file()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    child = sub.add_parser("score")
    child.add_argument("--root", type=Path, default=Path.cwd())
    child.add_argument("--skill", required=True)
    child = sub.add_parser("score-all")
    child.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        result = score_skill(args.root, args.skill) if args.command == "score" else score_all(args.root)
    except (SkillWorkbenchError, OSError, ValueError) as exc:
        print(f"Creator Skill Workbench failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
