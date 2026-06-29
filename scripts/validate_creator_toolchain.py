#!/usr/bin/env python3
"""Validate Creator Toolchain repository, state, and plugin contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from package_integrity import build_integrity_report, check_integrity_report
    from sync_plugin_skills import SKILLS, SyncError, synchronize
except ImportError:  # Imported as scripts.validate_creator_toolchain in tests.
    from scripts.package_integrity import build_integrity_report, check_integrity_report
    from scripts.sync_plugin_skills import SKILLS, SyncError, synchronize


ROOT = Path(__file__).resolve().parents[1]
CURRENT_STATE_SCHEMA = "0.3.0"
CURRENT_PLUGIN_VERSION = "1.0.1"
CURRENT_PUBLISHER = "crizleung21"

PROJECT_TYPES = (
    "slide-deck",
    "ai-image-system",
    "characterlock-system",
    "headlock-system",
    "ai-video-system",
    "prompt-pack",
    "character-registry",
    "content-campaign",
    "creator-tooling",
    "application",
    "workflow",
    "utility",
    "research-system",
)

REPO_REQUIRED_FILES = (
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "docs/architecture/creator-toolchain.md",
    "docs/architecture/state-contract.md",
    "docs/qa/capability-matrix.md",
    "docs/qa/skill-contract-tests.md",
    "docs/qa/package-integrity.md",
    "docs/qa/package-integrity-report.json",
    "docs/qa/behavior-acceptance-cases.json",
    "docs/qa/behavior-acceptance-report.json",
    "docs/fixtures/intake/character-image-slide-project.md",
    "scripts/materialize_project_type_refs.py",
    "scripts/sync_plugin_skills.py",
    "scripts/package_integrity.py",
    "scripts/build_plugin_package.py",
    "scripts/validate_creator_toolchain.py",
)

STATE_FILES = (
    ".creator/workspace.json",
    ".creator/projects.json",
    ".creator/entities.json",
    ".creator/state.json",
    ".creator/session-insights.json",
    ".creator/operator.json",
    ".creator/backlog.json",
    ".creator/surfaces.json",
    ".creator/decisions.json",
    ".creator/rules.json",
)

STATE_PRIVACY_CLASSES = {
    ".creator/workspace.json": "publishable_template",
    ".creator/projects.json": "repository_workflow_state",
    ".creator/entities.json": "private",
    ".creator/state.json": "repository_workflow_state",
    ".creator/session-insights.json": "private",
    ".creator/operator.json": "private",
    ".creator/backlog.json": "repository_workflow_state",
    ".creator/surfaces.json": "publishable_template",
    ".creator/decisions.json": "repository_workflow_state",
    ".creator/rules.json": "repository_contract",
}

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


@dataclass(frozen=True, order=True)
class Finding:
    check_id: str
    scope: str
    path: str
    message: str


def _finding(check_id: str, scope: str, path: Path | str, message: str) -> Finding:
    return Finding(check_id, scope, str(path), message)


def _read_json(path: Path, scope: str, check_id: str) -> tuple[Any | None, list[Finding]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [_finding(check_id, scope, path, f"invalid JSON: {exc}")]


def _frontmatter_findings(path: Path, expected_name: str, scope: str) -> list[Finding]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [_finding("SKILL_FILE", scope, path, f"cannot read skill: {exc}")]
    if not lines or lines[0] != "---":
        return [_finding("SKILL_FRONTMATTER", scope, path, "frontmatter must start with ---")]
    try:
        closing = lines.index("---", 1)
    except ValueError:
        return [_finding("SKILL_FRONTMATTER", scope, path, "frontmatter closing delimiter is missing")]

    values: dict[str, str] = {}
    findings: list[Finding] = []
    for line in lines[1:closing]:
        if not line.strip():
            continue
        if ":" not in line:
            findings.append(_finding("SKILL_FRONTMATTER", scope, path, f"invalid line: {line}"))
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in values:
            findings.append(_finding("SKILL_FRONTMATTER", scope, path, f"duplicate key: {key}"))
        values[key] = value
    if values.get("name") != expected_name:
        findings.append(
            _finding(
                "SKILL_FRONTMATTER",
                scope,
                path,
                f"name must be {expected_name!r}",
            )
        )
    if not values.get("description"):
        findings.append(_finding("SKILL_FRONTMATTER", scope, path, "description must be non-empty"))
    return findings


def validate_repo_contract(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    for relative in REPO_REQUIRED_FILES:
        if not (root / relative).is_file():
            findings.append(_finding("REPO_REQUIRED", "repo", relative, "required file is missing"))

    skill_root = root / ".agents/skills"
    found_skills = (
        {path.name for path in skill_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
        if skill_root.is_dir()
        else set()
    )
    if found_skills != set(SKILLS):
        findings.append(
            _finding(
                "REPO_SKILL_COUNT",
                "repo",
                skill_root,
                f"expected {len(SKILLS)} skills, found {sorted(found_skills)}",
            )
        )

    reference_re = re.compile(r"`(references/[A-Za-z0-9_./-]+\.(?:md|json))`")
    for skill in SKILLS:
        skill_file = skill_root / skill / "SKILL.md"
        if not skill_file.is_file():
            findings.append(_finding("SKILL_FILE", "repo", skill_file, "SKILL.md is missing"))
            continue
        findings.extend(_frontmatter_findings(skill_file, skill, "repo"))
        text = skill_file.read_text(encoding="utf-8")
        for reference in sorted(set(reference_re.findall(text))):
            reference_path = skill_file.parent / reference
            if not reference_path.is_file():
                findings.append(
                    _finding("SKILL_REFERENCE", "repo", reference_path, "referenced file is missing")
                )

    type_root = skill_root / "creator-intake-planner/references/types"
    found_types = {path.name for path in type_root.iterdir() if path.is_dir()} if type_root.is_dir() else set()
    if found_types != set(PROJECT_TYPES):
        findings.append(
            _finding(
                "PROJECT_TYPE_COUNT",
                "repo",
                type_root,
                f"expected {len(PROJECT_TYPES)} types, found {sorted(found_types)}",
            )
        )
    for type_id in PROJECT_TYPES:
        for filename in ("guide.md", "config.md", "skill-loadout.md"):
            path = type_root / type_id / filename
            if not path.is_file():
                findings.append(_finding("PROJECT_TYPE_FILE", "repo", path, "type reference is missing"))

    plugin_skill_root = root / "plugin/creator-toolchain/skills"
    if plugin_skill_root.is_dir() and skill_root.is_dir():
        try:
            parity = synchronize(skill_root, plugin_skill_root, write=False)
        except SyncError as exc:
            parity = [str(exc)]
        findings.extend(
            _finding("MIRROR_PARITY", "repo", plugin_skill_root, message) for message in parity
        )
    return sorted(set(findings))


def validate_state_contract(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    parsed: dict[str, Any] = {}
    for relative in STATE_FILES:
        path = root / relative
        if not path.is_file():
            findings.append(_finding("STATE_REQUIRED", "state", relative, "required state file is missing"))
            continue
        data, errors = _read_json(path, "state", "STATE_JSON")
        findings.extend(errors)
        if data is None:
            continue
        parsed[relative] = data
        if not isinstance(data, dict) or data.get("schema_version") != CURRENT_STATE_SCHEMA:
            findings.append(
                _finding(
                    "STATE_SCHEMA_VERSION",
                    "state",
                    relative,
                    f"schema_version must be {CURRENT_STATE_SCHEMA}",
                )
            )
        expected_owner = "creator-rule-router" if relative == ".creator/rules.json" else "creator-workspace-manager"
        if isinstance(data, dict) and data.get("owner_skill") != expected_owner:
            findings.append(_finding("STATE_OWNER", "state", relative, f"owner_skill must be {expected_owner}"))
        expected_privacy = STATE_PRIVACY_CLASSES[relative]
        if isinstance(data, dict) and data.get("privacy_class") != expected_privacy:
            findings.append(
                _finding(
                    "STATE_PRIVACY",
                    "state",
                    relative,
                    f"privacy_class must be {expected_privacy}",
                )
            )

    workspace = parsed.get(".creator/workspace.json", {})
    if isinstance(workspace, dict):
        architecture_map = workspace.get("architecture_map")
        if not isinstance(architecture_map, str) or not (root / architecture_map).is_file():
            findings.append(
                _finding(
                    "STATE_POINTER",
                    "state",
                    ".creator/workspace.json",
                    f"architecture_map target is missing: {architecture_map}",
                )
            )
        active_plan = workspace.get("active_plan")
        if active_plan is not None and (
            not isinstance(active_plan, str) or not (root / active_plan).is_file()
        ):
            findings.append(
                _finding(
                    "STATE_POINTER",
                    "state",
                    ".creator/workspace.json",
                    f"active_plan target is missing: {active_plan}",
                )
            )
        if workspace.get("state_contract") != ".creator/*.json":
            findings.append(
                _finding(
                    "STATE_FIELD",
                    "state",
                    ".creator/workspace.json",
                    "state_contract must be .creator/*.json",
                )
            )

    surfaces = parsed.get(".creator/surfaces.json", {})
    if isinstance(surfaces, dict):
        for surface in surfaces.get("surfaces", []):
            if not isinstance(surface, dict) or not surface.get("required"):
                continue
            value = surface.get("path")
            if not isinstance(value, str) or not (root / value).is_file():
                findings.append(
                    _finding(
                        "STATE_POINTER",
                        "state",
                        ".creator/surfaces.json",
                        f"surface target is missing: {value}",
                    )
                )

    projects = parsed.get(".creator/projects.json", {})
    project_ids: set[str] = set()
    if isinstance(projects, dict):
        for project in projects.get("projects", []):
            if not isinstance(project, dict):
                continue
            project_id = project.get("project_id")
            if isinstance(project_id, str):
                project_ids.add(project_id)
            for key in ("plan_path", "last_summary"):
                value = project.get(key)
                if value is not None and (
                    not isinstance(value, str) or not (root / value).is_file()
                ):
                    findings.append(
                        _finding(
                            "STATE_POINTER",
                            "state",
                            ".creator/projects.json",
                            f"{key} target is missing: {value}",
                        )
                    )

    state = parsed.get(".creator/state.json", {})
    if isinstance(state, dict):
        if not isinstance(state.get("last_health_check"), str):
            findings.append(
                _finding("STATE_FIELD", "state", ".creator/state.json", "last_health_check is required")
            )
        if not isinstance(state.get("state_divergence"), dict):
            findings.append(
                _finding("STATE_FIELD", "state", ".creator/state.json", "state_divergence is required")
            )
        active = {item for item in state.get("active_projects", []) if isinstance(item, str)}
        unknown = sorted(active - project_ids)
        if unknown:
            findings.append(
                _finding("STATE_PROJECT", "state", ".creator/state.json", f"unknown active projects: {unknown}")
            )

    decisions = parsed.get(".creator/decisions.json", {})
    decision_items = decisions.get("decisions", []) if isinstance(decisions, dict) else []
    decision_ids = {
        item.get("decision_id")
        for item in decision_items
        if isinstance(item, dict) and isinstance(item.get("decision_id"), str)
    }
    rules = parsed.get(".creator/rules.json", {})
    if isinstance(rules, dict):
        domains = rules.get("domains", [])
        if not any(isinstance(domain, dict) and domain.get("domain_id") == "GLOBAL" for domain in domains):
            findings.append(_finding("RULE_GLOBAL", "state", ".creator/rules.json", "GLOBAL domain is required"))
        if "staged_proposals" not in rules:
            findings.append(
                _finding("RULE_STAGING", "state", ".creator/rules.json", "staged_proposals is required")
            )
        if "decision_log" not in rules:
            findings.append(
                _finding("RULE_DECISIONS", "state", ".creator/rules.json", "decision_log is required")
            )
        for domain in domains:
            if not isinstance(domain, dict):
                continue
            unknown_refs = sorted(
                ref
                for ref in domain.get("decision_refs", [])
                if isinstance(ref, str) and ref not in decision_ids
            )
            if unknown_refs:
                findings.append(
                    _finding(
                        "RULE_DECISION_REF",
                        "state",
                        ".creator/rules.json",
                        f"unknown decision refs: {unknown_refs}",
                    )
                )
    return sorted(set(findings))


def validate_plugin_package(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    package_root = root / "plugin/creator-toolchain"
    if not package_root.is_dir():
        return [_finding("PLUGIN_ROOT", "plugin", package_root, "plugin package is missing")]

    manifest_path = package_root / ".codex-plugin/plugin.json"
    manifest, errors = _read_json(manifest_path, "plugin", "MANIFEST_JSON")
    findings.extend(errors)
    if isinstance(manifest, dict):
        for field in ("name", "version", "description", "author", "license", "skills", "interface"):
            if field not in manifest:
                findings.append(_finding("MANIFEST_FIELD", "plugin", manifest_path, f"missing field: {field}"))
        if manifest.get("name") != "creator-toolchain":
            findings.append(_finding("MANIFEST_NAME", "plugin", manifest_path, "name must be creator-toolchain"))
        version = manifest.get("version")
        if not isinstance(version, str) or not SEMVER_RE.fullmatch(version) or version != CURRENT_PLUGIN_VERSION:
            findings.append(
                _finding(
                    "MANIFEST_VERSION",
                    "plugin",
                    manifest_path,
                    f"version must be {CURRENT_PLUGIN_VERSION}",
                )
            )
        if manifest.get("license") != "MIT":
            findings.append(_finding("MANIFEST_LICENSE", "plugin", manifest_path, "license must be MIT"))
        author = manifest.get("author")
        interface = manifest.get("interface")
        if (
            not isinstance(author, dict)
            or author.get("name") != CURRENT_PUBLISHER
            or not isinstance(interface, dict)
            or interface.get("developerName") != CURRENT_PUBLISHER
        ):
            findings.append(
                _finding(
                    "MANIFEST_PUBLISHER",
                    "plugin",
                    manifest_path,
                    f"publisher fields must be {CURRENT_PUBLISHER}",
                )
            )
        if manifest.get("skills") != "./skills/":
            findings.append(_finding("MANIFEST_SKILLS", "plugin", manifest_path, "skills must be ./skills/"))

    marketplace_path = root / ".agents/plugins/marketplace.json"
    marketplace, errors = _read_json(marketplace_path, "plugin", "MARKETPLACE_JSON")
    findings.extend(errors)
    if isinstance(marketplace, dict):
        if marketplace.get("name") != "creator-toolchain":
            findings.append(
                _finding("MARKETPLACE_NAME", "plugin", marketplace_path, "name must be creator-toolchain")
            )
        plugins = marketplace.get("plugins", [])
        entry = next(
            (item for item in plugins if isinstance(item, dict) and item.get("name") == "creator-toolchain"),
            None,
        )
        if entry is None:
            findings.append(
                _finding("MARKETPLACE_ENTRY", "plugin", marketplace_path, "creator-toolchain entry is missing")
            )
        else:
            source = entry.get("source", {})
            policy = entry.get("policy", {})
            if source != {"source": "local", "path": "./plugin/creator-toolchain"}:
                findings.append(
                    _finding("MARKETPLACE_SOURCE", "plugin", marketplace_path, "local source path is invalid")
                )
            if policy.get("installation") != "AVAILABLE" or policy.get("authentication") != "ON_INSTALL":
                findings.append(
                    _finding(
                        "MARKETPLACE_POLICY",
                        "plugin",
                        marketplace_path,
                        "policy must be AVAILABLE/ON_INSTALL",
                    )
                )
            if entry.get("category") != "Productivity":
                findings.append(
                    _finding("MARKETPLACE_CATEGORY", "plugin", marketplace_path, "category must be Productivity")
                )

    root_license = root / "LICENSE"
    plugin_license = package_root / "LICENSE"
    if not root_license.is_file() or not plugin_license.is_file():
        findings.append(_finding("LEGAL_FILE", "plugin", "LICENSE", "root and plugin licenses are required"))
    elif root_license.read_bytes() != plugin_license.read_bytes():
        findings.append(_finding("LEGAL_PARITY", "plugin", "LICENSE", "root and plugin licenses must match"))

    current_report = build_integrity_report(root, package_root)
    for item in current_report.get("findings", []):
        if isinstance(item, dict):
            findings.append(
                _finding(
                    "PACKAGE_INTEGRITY",
                    "plugin",
                    item.get("path", package_root),
                    f"{item.get('check_id')}: {item.get('message')}",
                )
            )
    report_path = root / "docs/qa/package-integrity-report.json"
    for message in check_integrity_report(root, package_root, report_path):
        findings.append(_finding("PACKAGE_INTEGRITY_REPORT", "plugin", report_path, message))

    plugin_skill_root = package_root / "skills"
    for skill in SKILLS:
        skill_file = plugin_skill_root / skill / "SKILL.md"
        if not skill_file.is_file():
            findings.append(_finding("PLUGIN_SKILL", "plugin", skill_file, "plugin skill is missing"))
        else:
            findings.extend(_frontmatter_findings(skill_file, skill, "plugin"))
    return sorted(set(findings))


def validate_all(root: Path) -> list[Finding]:
    return sorted(
        set(
            validate_repo_contract(root)
            + validate_state_contract(root)
            + validate_plugin_package(root)
        )
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="all")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    if args.scope not in {"repo", "state", "plugin", "all"}:
        parser.error(f"invalid scope {args.scope!r}; choose repo, state, plugin, or all")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    validators = {
        "repo": validate_repo_contract,
        "state": validate_state_contract,
        "plugin": validate_plugin_package,
        "all": validate_all,
    }
    findings = validators[args.scope](args.root)
    if findings:
        for finding in findings:
            print(f"FAIL [{finding.scope}:{finding.check_id}] {finding.path}: {finding.message}")
        return 1
    print(f"Creator Toolchain {args.scope} validation passed.")
    if args.scope in {"repo", "all"}:
        print(f"Validated {len(SKILLS)} authoritative skills and {len(PROJECT_TYPES)} project types.")
    if args.scope in {"plugin", "all"}:
        print("Validated plugin manifest, marketplace, exact package integrity, and mirror parity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
