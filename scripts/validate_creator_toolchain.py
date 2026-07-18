#!/usr/bin/env python3
"""Validate Creator Toolchain repository, state, and plugin contracts."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from creator_schema_validation import SCHEMAS as SCHEMA_PATHS, validate_workspace
    from creator_state_store import STATE_FILES
    from materialize_project_type_refs import synchronize as synchronize_project_types
    from package_integrity import build_integrity_report, check_integrity_report
    from sync_plugin_skills import SKILLS, SyncError, synchronize
except ImportError:  # Imported as scripts.validate_creator_toolchain in tests.
    from scripts.creator_schema_validation import SCHEMAS as SCHEMA_PATHS, validate_workspace
    from scripts.creator_state_store import STATE_FILES
    from scripts.materialize_project_type_refs import synchronize as synchronize_project_types
    from scripts.package_integrity import build_integrity_report, check_integrity_report
    from scripts.sync_plugin_skills import SKILLS, SyncError, synchronize

ROOT = Path(__file__).resolve().parents[1]
CURRENT_STATE_SCHEMA = "0.4.0"
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
PROJECT_SCHEMA_PATHS = (
    "schemas/project/project.schema.json",
    "schemas/project/intake-state.schema.json",
    "schemas/project/handoff.schema.json",
    "schemas/project/ledger-event.schema.json",
    "schemas/project/state-registration-proposal.schema.json",
    "schemas/project/execution-handoff.schema.json",
)
REPO_REQUIRED_FILES = (
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "IMPLEMENTATION__PLAN.md",
    "config/project-types.json",
    "docs/architecture/creator-toolchain.md",
    "docs/architecture/state-contract.md",
    "docs/qa/capability-matrix.md",
    "docs/qa/skill-contract-tests.md",
    "docs/qa/package-integrity.md",
    "docs/qa/package-integrity-report.json",
    "docs/qa/behavior-acceptance-cases.json",
    "docs/qa/behavior-acceptance-report.json",
    "docs/qa/behavior-acceptance-status.json",
    "docs/fixtures/intake/character-image-slide-project.md",
    "docs/migrations/0.3.0-to-0.4.0.md",
    "scripts/materialize_project_type_refs.py",
    "scripts/sync_plugin_skills.py",
    "scripts/package_integrity.py",
    "scripts/build_plugin_package.py",
    "scripts/validate_creator_toolchain.py",
    "scripts/bootstrap_creator_workspace.py",
    "scripts/creator_state_store.py",
    "scripts/creator_transactions.py",
    "scripts/creator_ids.py",
    "scripts/creator_ledger.py",
    "scripts/json_schema_lite.py",
    "scripts/migrate_creator_state.py",
    "scripts/creator_intake_artifacts.py",
    "scripts/creator_intake_workflow.py",
    "scripts/creator_planning_gate.py",
    "scripts/creator_project_types.py",
) + tuple(SCHEMA_PATHS.values()) + PROJECT_SCHEMA_PATHS
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
        findings.append(_finding("SKILL_FRONTMATTER", scope, path, f"name must be {expected_name!r}"))
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
    found = (
        {path.name for path in skill_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()}
        if skill_root.is_dir()
        else set()
    )
    if found != set(SKILLS):
        findings.append(
            _finding(
                "REPO_SKILL_COUNT",
                "repo",
                skill_root,
                f"expected {len(SKILLS)} skills, found {sorted(found)}",
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
            if not (skill_file.parent / reference).is_file():
                findings.append(
                    _finding("SKILL_REFERENCE", "repo", skill_file.parent / reference, "referenced file is missing")
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
    for message in synchronize_project_types(root, write=False):
        findings.append(_finding("PROJECT_TYPE_MATERIALIZATION", "repo", type_root, message))

    plugin_root = root / "plugin/creator-toolchain/skills"
    if plugin_root.is_dir() and skill_root.is_dir():
        try:
            parity = synchronize(skill_root, plugin_root, write=False)
        except SyncError as exc:
            parity = [str(exc)]
        findings.extend(_finding("MIRROR_PARITY", "repo", plugin_root, message) for message in parity)
    return sorted(set(findings))


def _state_check_id(message: str) -> str:
    text = message.lower()
    if "schema" in text:
        return "STATE_SCHEMA"
    if "owner_skill" in text:
        return "STATE_OWNER"
    if "privacy_class" in text:
        return "STATE_PRIVACY"
    if "missing state surface" in text:
        return "STATE_REQUIRED"
    if any(token in text for token in ("pointer", "target is missing", "architecture_map", "active_plan")):
        return "STATE_POINTER"
    if "unknown state project" in text:
        return "STATE_PROJECT"
    if "decision ref" in text:
        return "RULE_DECISION_REF"
    if "surface registry" in text:
        return "STATE_SURFACE_REGISTRY"
    if "duplicate" in text:
        return "STATE_DUPLICATE_ID"
    return "STATE_CONTRACT"


def validate_state_contract(root: Path) -> list[Finding]:
    root = root.resolve()
    return sorted(
        {
            _finding(_state_check_id(message), "state", ".creator", message)
            for message in validate_workspace(root, schema_root=ROOT)
        }
    )


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
                _finding("MANIFEST_VERSION", "plugin", manifest_path, f"version must be {CURRENT_PLUGIN_VERSION}")
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
            findings.append(_finding("MARKETPLACE_NAME", "plugin", marketplace_path, "name must be creator-toolchain"))
        entry = next(
            (
                item
                for item in marketplace.get("plugins", [])
                if isinstance(item, dict) and item.get("name") == "creator-toolchain"
            ),
            None,
        )
        if entry is None:
            findings.append(
                _finding("MARKETPLACE_ENTRY", "plugin", marketplace_path, "creator-toolchain entry is missing")
            )
        else:
            if entry.get("source") != {"source": "local", "path": "./plugin/creator-toolchain"}:
                findings.append(
                    _finding("MARKETPLACE_SOURCE", "plugin", marketplace_path, "local source path is invalid")
                )
            policy = entry.get("policy", {})
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

    report = build_integrity_report(root, package_root)
    for item in report.get("findings", []):
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
    findings.extend(
        _finding("PACKAGE_INTEGRITY_REPORT", "plugin", report_path, message)
        for message in check_integrity_report(root, package_root, report_path)
    )
    for skill in SKILLS:
        skill_file = package_root / "skills" / skill / "SKILL.md"
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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
    validator = {
        "repo": validate_repo_contract,
        "state": validate_state_contract,
        "plugin": validate_plugin_package,
        "all": validate_all,
    }[args.scope]
    findings = validator(args.root)
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
