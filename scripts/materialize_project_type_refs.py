#!/usr/bin/env python3
"""Materialize domain-specific Intake references from config/project-types.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from creator_project_types import ProjectTypeError, load_project_types
except ImportError:  # Imported as scripts.materialize_project_type_refs in tests.
    from scripts.creator_project_types import ProjectTypeError, load_project_types

ROOT = Path(__file__).resolve().parents[1]
TYPE_ROOT_RELATIVE = Path(".agents/skills/creator-intake-planner/references/types")


def _bullets(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values)


def _secondary_skills(contract: dict[str, object]) -> list[str]:
    skills = ["creator-execution-cycle"]
    rule_domains = contract["rule_domains"]
    audit_domains = contract["audit_domains"]
    if isinstance(rule_domains, list) and any(item != "GLOBAL" for item in rule_domains):
        skills.append("creator-rule-router")
    if isinstance(audit_domains, list) and audit_domains:
        skills.append("creator-evidence-audit")
    if contract["type_id"] in {"creator-tooling", "prompt-pack"}:
        skills.append("creator-skill-workbench")
    if contract["type_id"] == "character-registry":
        skills.append("creator-workspace-manager")
    return list(dict.fromkeys(skills))


def render_reference_set(contract: dict[str, object]) -> dict[str, str]:
    type_id = str(contract["type_id"])
    rigor = str(contract["rigor"])
    purpose = str(contract["purpose"])
    inputs = list(contract["inputs"])
    deliverables = list(contract["deliverables"])
    acceptance = list(contract["acceptance_patterns"])
    risks = list(contract["risk_checklist"])
    rule_domains = list(contract["rule_domains"])
    audit_domains = list(contract["audit_domains"])
    example = str(contract["example"])
    secondary = _secondary_skills(contract)
    guide = f"""# {type_id} Guide

## Purpose

{purpose}

## Required Inputs

{_bullets(inputs)}

## Expected Deliverables

{_bullets(deliverables)}

## Observable Acceptance Patterns

{_bullets(acceptance)}

## Discovery Questions

- Which required inputs are already available?
- Which deliverables are mandatory for the accepted MVP?
- Which acceptance patterns can be verified deterministically?
- Which risks require explicit guardrails or rollback?
- What is explicitly out of scope?

## Risk Checklist

{_bullets(risks)}

## Example

{example}

## Boundary

Do not implement this project type inside Intake. Produce the canonical planning package, pass the Planning Quality Gate, and require explicit approval.
"""
    config = f"""# {type_id} Config

- rigor: `{rigor}`
- minimum_acceptance_criteria: `3`
- default_handoff: `creator-execution-cycle`
- example: `{example}`

## Required Sections

- Goal
- Project Type
- Context
- Source Assets
- Scope
- Out of Scope
- Acceptance Criteria
- Risks
- Open Questions
- Handoff Target

## Inputs

{_bullets(inputs)}

## Deliverables

{_bullets(deliverables)}

## Acceptance Patterns

{_bullets(acceptance)}

## Risk Checklist

{_bullets(risks)}

## Rule Domains

{_bullets([f'`{item}`' for item in rule_domains])}

## Audit Domains

{_bullets(audit_domains)}
"""
    loadout = f"""# {type_id} Skill Loadout

## Primary Skill

`creator-intake-planner`

## Secondary Skills

{_bullets([f'`{item}`' for item in secondary])}

## Rule Domains

{_bullets([f'`{item}`' for item in rule_domains])}

## Audit Domains

{_bullets(audit_domains)}

## State Surfaces

- `.creator/plans/{{project_slug}}/`
- `.creator/state-proposals/{{project_id}}.json`
- `.creator/projects.json` through a staged proposal owned by `creator-workspace-manager`

## Handoff

After an explicit `handoff-to-execution` approval, generate `.creator/handoffs/{{project_id}}.json` for `creator-execution-cycle`.
"""
    return {"guide.md": guide, "config.md": config, "skill-loadout.md": loadout}


def expected_files(root: Path = ROOT) -> dict[Path, str]:
    contracts = load_project_types(root)
    result: dict[Path, str] = {}
    for type_id in sorted(contracts):
        for filename, content in render_reference_set(contracts[type_id]).items():
            result[TYPE_ROOT_RELATIVE / type_id / filename] = content
    return result


def synchronize(root: Path = ROOT, *, write: bool) -> list[str]:
    findings: list[str] = []
    try:
        expected = expected_files(root)
    except (ProjectTypeError, OSError, ValueError) as exc:
        return [f"cannot materialize project-type references: {exc}"]
    for relative, expected_content in expected.items():
        path = Path(root) / relative
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual == expected_content:
            continue
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected_content, encoding="utf-8")
        else:
            findings.append(f"stale project-type reference: {relative.as_posix()}")
    return findings


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    findings = synchronize(args.root, write=args.write)
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        return 1
    action = "Materialized" if args.write else "Validated"
    print(f"{action} 13 project-type reference sets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
