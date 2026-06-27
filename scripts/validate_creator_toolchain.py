#!/usr/bin/env python3
"""Validate the Creator Toolchain scaffold.

This validator checks repository artifacts, JSON state surfaces, skill metadata,
and plugin packaging hygiene. It intentionally does not validate the live Codex
plugin schema; that remains a Phase 5 external freshness gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "IMPLEMENTATION_PLAN.md",
    "docs/archive/plans/IMPLEMENTATION_PLAN.v0.4.1.md",
    "docs/archive/audits/SOURCE_TRACEABILITY_AND_AUDIT.md",
    "docs/source-analysis/christopherkahler-toolchain-map.md",
    "docs/archive/phase-1/phase-1-test-prompts.md",
    "docs/archive/phase-1/phase-1-acceptance-checklist.md",
    "docs/fixtures/seed/character-image-slide-project.md",
    ".creator/workspace.json",
    ".creator/projects.json",
    ".creator/entities.json",
    ".creator/state.json",
    ".creator/psmm.json",
    ".creator/operator.json",
    ".creator/backlog.json",
    ".creator/surfaces.json",
    ".creator/decisions.json",
    ".creator/rules.json",
    ".creator/plans/creator-toolchain-implementation/project.json",
    ".creator/plans/creator-toolchain-implementation/activity_ledger.jsonl",
    ".creator/plans/creator-toolchain-implementation/PLANNING.md",
    ".creator/plans/creator-toolchain-implementation/SEED-STATE.md",
    ".creator/plans/creator-toolchain-implementation/HANDOFF.md",
    ".creator/plans/creator-toolchain-implementation/PLAN-001.md",
    ".creator/plans/creator-toolchain-implementation/UNIFY-001.md",
    ".creator/plans/creator-toolchain-implementation/SUMMARY-001.md",
    ".agents/plugins/marketplace.json",
    "plugin/creator-toolchain/.codex-plugin/plugin.json",
    "plugin/creator-toolchain/README.md",
    "plugin/creator-toolchain/release-evidence/manifest-schema-validation.md",
    "plugin/creator-toolchain/release-evidence/package-contents-audit.md",
    "plugin/creator-toolchain/release-evidence/privacy-sanitization-audit.md",
    "scripts/validate_creator_toolchain.py",
    "scripts/materialize_seed_type_refs.py",
]

SKILLS = [
    "creator-orchestrator",
    "creator-seed-incubator",
    "creator-paul-loop",
    "creator-base-workspace",
    "creator-rule-router",
    "creator-skillsmith-factory",
    "creator-aegis-audit",
]

SEED_TYPES = [
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
]

JSON_FILES = [
    ".creator/workspace.json",
    ".creator/projects.json",
    ".creator/entities.json",
    ".creator/state.json",
    ".creator/psmm.json",
    ".creator/operator.json",
    ".creator/backlog.json",
    ".creator/surfaces.json",
    ".creator/decisions.json",
    ".creator/rules.json",
    ".creator/plans/creator-toolchain-implementation/project.json",
    "plugin/creator-toolchain/.codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
]

DISALLOWED_PACKAGE_PARTS = {"upstream", ".creator", ".DS_Store", "__pycache__"}
SCHEMA_VERSION_EXEMPT = {
    "plugin/creator-toolchain/.codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_required_files(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.exists():
            fail(f"missing required file: {rel}", errors)


def validate_json(errors: list[str]) -> None:
    for rel in JSON_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            data = json.loads(read_text(path))
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON {rel}: {exc}", errors)
            continue
        if "schema_version" not in data and rel not in SCHEMA_VERSION_EXEMPT:
            fail(f"missing schema_version in {rel}", errors)


def validate_jsonl(errors: list[str]) -> None:
    rel = ".creator/plans/creator-toolchain-implementation/activity_ledger.jsonl"
    path = ROOT / rel
    if not path.exists():
        return
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSONL {rel}:{idx}: {exc}", errors)


def validate_skills(errors: list[str]) -> None:
    for skill in SKILLS:
        for base in [ROOT / ".agents/skills", ROOT / "plugin/creator-toolchain/skills"]:
            path = base / skill / "SKILL.md"
            if not path.exists():
                fail(f"missing SKILL.md: {path.relative_to(ROOT)}", errors)
                continue
            text = read_text(path)
            if not text.startswith("---\n"):
                fail(f"missing YAML frontmatter: {path.relative_to(ROOT)}", errors)
            if f"name: {skill}" not in text:
                fail(f"frontmatter name mismatch in {path.relative_to(ROOT)}", errors)
            if "description:" not in text:
                fail(f"missing description in {path.relative_to(ROOT)}", errors)


def validate_seed_types(errors: list[str]) -> None:
    bases = [
        ROOT / ".agents/skills/creator-seed-incubator/references/types",
        ROOT / "plugin/creator-toolchain/skills/creator-seed-incubator/references/types",
    ]
    for base in bases:
        for type_id in SEED_TYPES:
            for filename in ["guide.md", "config.md", "skill-loadout.md"]:
                path = base / type_id / filename
                if not path.exists():
                    fail(f"missing SEED type reference: {path.relative_to(ROOT)}", errors)


def validate_rules(errors: list[str]) -> None:
    path = ROOT / ".creator/rules.json"
    if not path.exists():
        return
    data = json.loads(read_text(path))
    domains = data.get("domains", [])
    if not any(domain.get("domain_id") == "GLOBAL" for domain in domains):
        fail("rules.json missing GLOBAL domain", errors)
    if "staged_proposals" not in data:
        fail("rules.json missing staged_proposals", errors)
    if "decision_log" not in data:
        fail("rules.json missing decision_log", errors)


def validate_plugin(errors: list[str]) -> None:
    manifest = ROOT / "plugin/creator-toolchain/.codex-plugin/plugin.json"
    if manifest.exists():
        data = json.loads(read_text(manifest))
        for key in ["name", "version", "description", "skills", "interface"]:
            if key not in data:
                fail(f"plugin manifest missing key: {key}", errors)
        if data.get("skills") != "./skills/":
            fail("plugin manifest skills path must be ./skills/", errors)
    marketplace = ROOT / ".agents/plugins/marketplace.json"
    if marketplace.exists():
        data = json.loads(read_text(marketplace))
        plugins = data.get("plugins", [])
        if not any(plugin.get("name") == "creator-toolchain" for plugin in plugins):
            fail("marketplace missing creator-toolchain entry", errors)
        for plugin in plugins:
            if plugin.get("name") == "creator-toolchain":
                source = plugin.get("source", {})
                if source.get("source") != "local":
                    fail("creator-toolchain marketplace source must be local", errors)
                if source.get("path") != "./plugin/creator-toolchain":
                    fail("creator-toolchain marketplace path must be ./plugin/creator-toolchain", errors)
                policy = plugin.get("policy", {})
                if policy.get("installation") != "AVAILABLE":
                    fail("creator-toolchain marketplace installation policy must be AVAILABLE", errors)
                if policy.get("authentication") != "ON_INSTALL":
                    fail("creator-toolchain marketplace authentication policy must be ON_INSTALL", errors)
                if plugin.get("category") != "Productivity":
                    fail("creator-toolchain marketplace category must be Productivity", errors)
    package_root = ROOT / "plugin/creator-toolchain"
    if package_root.exists():
        for path in package_root.rglob("*"):
            parts = set(path.relative_to(package_root).parts)
            if parts & DISALLOWED_PACKAGE_PARTS:
                fail(f"disallowed package path: {path.relative_to(ROOT)}", errors)


def validate_workspace_hygiene(errors: list[str]) -> None:
    for path in ROOT.rglob(".DS_Store"):
        if "upstream" in path.relative_to(ROOT).parts:
            continue
        fail(f"disallowed workspace artifact: {path.relative_to(ROOT)}", errors)


def main() -> int:
    errors: list[str] = []
    validate_required_files(errors)
    validate_json(errors)
    validate_jsonl(errors)
    validate_skills(errors)
    validate_seed_types(errors)
    validate_rules(errors)
    validate_plugin(errors)
    validate_workspace_hygiene(errors)

    if errors:
        print("Creator Toolchain validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Creator Toolchain validation passed.")
    print(f"Validated {len(REQUIRED_FILES)} required files and {len(SKILLS)} skills.")
    print("Release note: repeat Codex plugin install and UI skill-selection tests before public release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
