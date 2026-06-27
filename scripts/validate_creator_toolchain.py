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
    from sync_plugin_skills import SKILLS, SyncError, synchronize
except ImportError:  # Imported as scripts.validate_creator_toolchain in tests.
    from scripts.sync_plugin_skills import SKILLS, SyncError, synchronize


ROOT = Path(__file__).resolve().parents[1]
CURRENT_STATE_SCHEMA = "0.2.0"
CURRENT_PLUGIN_VERSION = "1.0.0-draft.1"

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
    "README.md",
    "docs/source-analysis/upstream-toolchain-map.md",
    "docs/migrations/creator-native-naming-v1.md",
    "docs/qa/capability-matrix.md",
    "docs/qa/skill-contract-tests.md",
    "docs/fixtures/intake/character-image-slide-project.md",
    "scripts/materialize_project_type_refs.py",
    "scripts/sync_plugin_skills.py",
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

STALE_ACTIVE_PATHS = (
    "docs/phase-1-test-prompts.md",
    "docs/phase-1-acceptance-checklist.md",
    "docs/examples/character-image-slide-project.md",
)

LEGACY_ALLOWED_PREFIXES = (
    Path("docs/source-analysis"),
    Path("docs/archive"),
    Path("docs/migrations"),
    Path(".creator/plans/creator-toolchain-implementation"),
    Path(".creator/plans/creator-toolchain-stabilization"),
    Path(".creator/plans/creator-toolchain-naming-migration"),
)
LEGACY_ALLOWED_FILES = {
    Path(".creator/decisions.json"),
    Path(".creator/reports/stabilization-baseline.md"),
}
LEGACY_PATTERNS = (
    re.compile(r"creator-(?:seed-incubator|paul-loop|base-workspace|skillsmith-factory|aegis-audit)", re.I),
    re.compile(r"creator-(?:seed|paul|base):", re.I),
    re.compile(r"\b(?:SEED|PAUL|BASE|CARL|AEGIS|PSMM)\b"),
    re.compile(r"\bSkillsmith\b", re.I),
    re.compile(r"SEED-STATE\.md|UNIFY(?:-|\b)|Layer [ABC]\b"),
    re.compile(r"\b(?:pulse|groom|graduate|graduation)\b", re.I),
    re.compile(r"(?:materialize_seed|fixtures/seed|psmm\.json|last_pulse|\"drift\"\s*:)", re.I),
)

DISALLOWED_PACKAGE_NAMES = {
    ".agents",
    ".creator",
    ".DS_Store",
    ".env",
    ".git",
    ".gitkeep",
    "__pycache__",
    "package",
    "private",
    "upstream",
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


def _active_text_files(root: Path) -> list[Path]:
    paths = [root / "README.md", root / "AGENTS.md"]
    for relative in ("docs/qa", "scripts"):
        base = root / relative
        if not base.is_dir():
            continue
        paths.extend(
            path
            for path in base.rglob("*")
            if path.suffix in {".md", ".py"}
            and path.name != "validate_creator_toolchain.py"
        )
    return paths


def _legacy_name_findings(root: Path) -> list[Finding]:
    roots = (
        root / "README.md",
        root / "AGENTS.md",
        root / ".agents/skills",
        root / ".creator",
        root / "docs/qa",
        root / "docs/fixtures",
        root / "scripts",
        root / "plugin/creator-toolchain",
    )
    text_suffixes = {".json", ".jsonl", ".md", ".py", ".sha256", ".toml"}
    paths: set[Path] = set()
    for base in roots:
        if base.is_file():
            paths.add(base)
        elif base.is_dir():
            paths.update(path for path in base.rglob("*") if path.is_file())

    findings: list[Finding] = []
    for path in sorted(paths):
        relative = path.relative_to(root)
        if relative in LEGACY_ALLOWED_FILES:
            continue
        if any(relative == prefix or prefix in relative.parents for prefix in LEGACY_ALLOWED_PREFIXES):
            continue
        if relative == Path("scripts/validate_creator_toolchain.py"):
            continue
        if path.suffix not in text_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            findings.append(_finding("REPO_READ", "repo", relative, f"cannot read file: {exc}"))
            continue
        for pattern in LEGACY_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    _finding("LEGACY_NAME", "repo", relative, f"legacy product marker: {match.group(0)}")
                )
                break
    return findings


def validate_repo_contract(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []

    for relative in REPO_REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            findings.append(_finding("REPO_REQUIRED", "repo", relative, "required file is missing"))

    findings.extend(_legacy_name_findings(root))

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

    for path in _active_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(_finding("REPO_READ", "repo", path, f"cannot read file: {exc}"))
            continue
        for stale in STALE_ACTIVE_PATHS:
            if stale in text:
                findings.append(_finding("STALE_PATH", "repo", path, f"stale active path: {stale}"))

    plugin_skill_root = root / "plugin/creator-toolchain/skills"
    if plugin_skill_root.is_dir() and skill_root.is_dir():
        try:
            parity = synchronize(skill_root, plugin_skill_root, write=False)
        except SyncError as exc:
            parity = [str(exc)]
        for message in parity:
            findings.append(_finding("MIRROR_PARITY", "repo", plugin_skill_root, message))

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
        if not isinstance(data, dict) or not data.get("schema_version"):
            findings.append(_finding("STATE_SCHEMA", "state", relative, "schema_version is required"))
        elif data.get("schema_version") != CURRENT_STATE_SCHEMA:
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

    for path in sorted((root / ".creator/plans").glob("**/*.json")):
        data, errors = _read_json(path, "state", "STATE_JSON")
        findings.extend(errors)
        if data is not None and (not isinstance(data, dict) or not data.get("schema_version")):
            findings.append(_finding("STATE_SCHEMA", "state", path, "schema_version is required"))

    for path in sorted((root / ".creator/plans").glob("**/*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            findings.append(_finding("STATE_JSONL", "state", path, f"cannot read JSONL: {exc}"))
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                findings.append(
                    _finding("STATE_JSONL", "state", path, f"line {line_number}: {exc.msg}")
                )

    workspace = parsed.get(".creator/workspace.json", {})
    if isinstance(workspace, dict):
        for key in ("source_map", "active_plan"):
            value = workspace.get(key)
            if not isinstance(value, str) or not (root / value).is_file():
                findings.append(
                    _finding("STATE_POINTER", "state", ".creator/workspace.json", f"{key} target is missing: {value}")
                )

    surfaces = parsed.get(".creator/surfaces.json", {})
    if isinstance(surfaces, dict):
        for surface in surfaces.get("surfaces", []):
            if not isinstance(surface, dict) or not surface.get("required"):
                continue
            value = surface.get("path")
            if not isinstance(value, str) or not (root / value).is_file():
                findings.append(_finding("STATE_POINTER", "state", ".creator/surfaces.json", f"surface target is missing: {value}"))

    projects = parsed.get(".creator/projects.json", {})
    project_ids: set[str] = set()
    if isinstance(projects, dict):
        for project in projects.get("projects", []):
            if not isinstance(project, dict):
                continue
            project_id = project.get("project_id")
            if isinstance(project_id, str):
                project_ids.add(project_id)
            pointer_keys = ["plan_path"]
            if project.get("status") == "completed" or "last_summary" in project:
                pointer_keys.append("last_summary")
            for key in pointer_keys:
                value = project.get(key)
                if not isinstance(value, str) or not (root / value).is_file():
                    findings.append(_finding("STATE_POINTER", "state", ".creator/projects.json", f"{key} target is missing: {value}"))

    state = parsed.get(".creator/state.json", {})
    if isinstance(state, dict):
        if not isinstance(state.get("last_health_check"), str):
            findings.append(_finding("STATE_FIELD", "state", ".creator/state.json", "last_health_check is required"))
        if not isinstance(state.get("state_divergence"), dict):
            findings.append(_finding("STATE_FIELD", "state", ".creator/state.json", "state_divergence is required"))
        active = {item for item in state.get("active_projects", []) if isinstance(item, str)}
        unknown = sorted(active - project_ids)
        if unknown:
            findings.append(_finding("STATE_PROJECT", "state", ".creator/state.json", f"unknown active projects: {unknown}"))

    rules = parsed.get(".creator/rules.json", {})
    if isinstance(rules, dict):
        domains = rules.get("domains", [])
        if not any(isinstance(domain, dict) and domain.get("domain_id") == "GLOBAL" for domain in domains):
            findings.append(_finding("RULE_GLOBAL", "state", ".creator/rules.json", "GLOBAL domain is required"))
        if "staged_proposals" not in rules:
            findings.append(_finding("RULE_STAGING", "state", ".creator/rules.json", "staged_proposals is required"))
        if "decision_log" not in rules:
            findings.append(_finding("RULE_DECISIONS", "state", ".creator/rules.json", "decision_log is required"))

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
        for field in ("name", "version", "description", "skills", "interface"):
            if field not in manifest:
                findings.append(_finding("MANIFEST_FIELD", "plugin", manifest_path, f"missing field: {field}"))
        if manifest.get("name") != "creator-toolchain":
            findings.append(_finding("MANIFEST_NAME", "plugin", manifest_path, "name must be creator-toolchain"))
        version = manifest.get("version")
        if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
            findings.append(_finding("MANIFEST_VERSION", "plugin", manifest_path, "version must be strict semver"))
        elif version != CURRENT_PLUGIN_VERSION:
            findings.append(
                _finding("MANIFEST_VERSION", "plugin", manifest_path, f"version must be {CURRENT_PLUGIN_VERSION}")
            )
        if manifest.get("skills") != "./skills/":
            findings.append(_finding("MANIFEST_SKILLS", "plugin", manifest_path, "skills must be ./skills/"))
        if not isinstance(manifest.get("interface"), dict) or not manifest.get("interface"):
            findings.append(_finding("MANIFEST_INTERFACE", "plugin", manifest_path, "interface must be a non-empty object"))

    marketplace_path = root / ".agents/plugins/marketplace.json"
    marketplace, errors = _read_json(marketplace_path, "plugin", "MARKETPLACE_JSON")
    findings.extend(errors)
    if isinstance(marketplace, dict):
        plugins = marketplace.get("plugins", [])
        entry = next(
            (item for item in plugins if isinstance(item, dict) and item.get("name") == "creator-toolchain"),
            None,
        )
        if entry is None:
            findings.append(_finding("MARKETPLACE_ENTRY", "plugin", marketplace_path, "creator-toolchain entry is missing"))
        else:
            source = entry.get("source", {})
            policy = entry.get("policy", {})
            if source != {"source": "local", "path": "./plugin/creator-toolchain"}:
                findings.append(_finding("MARKETPLACE_SOURCE", "plugin", marketplace_path, "local source path is invalid"))
            if policy.get("installation") != "AVAILABLE" or policy.get("authentication") != "ON_INSTALL":
                findings.append(_finding("MARKETPLACE_POLICY", "plugin", marketplace_path, "policy must be AVAILABLE/ON_INSTALL"))
            if entry.get("category") != "Productivity":
                findings.append(_finding("MARKETPLACE_CATEGORY", "plugin", marketplace_path, "category must be Productivity"))

    resolved_package = package_root.resolve()
    for path in sorted(package_root.rglob("*")):
        relative = path.relative_to(package_root)
        parts = set(relative.parts)
        if ".creator" in parts or path.name.endswith(".local.json"):
            findings.append(_finding("PACKAGE_PRIVATE", "plugin", relative, "private state is prohibited"))
        elif (
            parts & DISALLOWED_PACKAGE_NAMES
            or path.suffix in {".pyc", ".zip"}
            or path.name.startswith(".env")
        ):
            findings.append(_finding("PACKAGE_ARTIFACT", "plugin", relative, "disallowed package artifact"))
        if path.is_symlink():
            try:
                path.resolve().relative_to(resolved_package)
            except ValueError:
                findings.append(_finding("PACKAGE_SYMLINK", "plugin", relative, "symlink escapes package root"))

    plugin_skill_root = package_root / "skills"
    for skill in SKILLS:
        skill_file = plugin_skill_root / skill / "SKILL.md"
        if not skill_file.is_file():
            findings.append(_finding("PLUGIN_SKILL", "plugin", skill_file, "plugin skill is missing"))
        else:
            findings.extend(_frontmatter_findings(skill_file, skill, "plugin"))

    source_root = root / ".agents/skills"
    try:
        parity = synchronize(source_root, plugin_skill_root, write=False)
    except SyncError as exc:
        parity = [str(exc)]
    for message in parity:
        findings.append(_finding("MIRROR_PARITY", "plugin", plugin_skill_root, message))

    return sorted(set(findings))


def validate_all(root: Path) -> list[Finding]:
    return sorted(
        validate_repo_contract(root)
        + validate_state_contract(root)
        + validate_plugin_package(root)
    )


def _parse_args(argv: list[str] | None) -> tuple[argparse.ArgumentParser, argparse.Namespace | None]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", default="all")
    parser.add_argument("--root", type=Path, default=ROOT)
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return parser, None
    return parser, args


def main(argv: list[str] | None = None) -> int:
    parser, args = _parse_args(argv)
    if args is None:
        return 2
    validators = {
        "repo": validate_repo_contract,
        "state": validate_state_contract,
        "plugin": validate_plugin_package,
        "all": validate_all,
    }
    if args.scope not in validators:
        parser.print_usage(sys.stderr)
        print(f"error: invalid scope {args.scope!r}; choose repo, state, plugin, or all", file=sys.stderr)
        return 2

    findings = validators[args.scope](args.root)
    if findings:
        print(f"Creator Toolchain {args.scope} validation failed ({len(findings)} findings):")
        for finding in findings:
            print(f"- [{finding.check_id}] {finding.path}: {finding.message}")
        return 1

    print(f"Creator Toolchain {args.scope} validation passed.")
    if args.scope in {"repo", "all"}:
        print(f"Validated {len(SKILLS)} authoritative skills and {len(PROJECT_TYPES)} project types.")
    if args.scope in {"plugin", "all"}:
        print("Validated plugin manifest, marketplace, mirror parity, and package hygiene.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
