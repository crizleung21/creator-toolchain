#!/usr/bin/env python3
"""Materialize SEED project type reference files.

The implementation plan requires each project type to define guide, config, and
skill loadout references. This script keeps those repetitive files consistent.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TYPE_ROOT = ROOT / ".agents/skills/creator-seed-incubator/references/types"

PROJECT_TYPES = {
    "slide-deck": ("standard", "presentation, pitch, or teaching deck", ["creator-seed-incubator", "creator-paul-loop"]),
    "ai-image-system": ("deep", "image generation workflow", ["creator-seed-incubator", "creator-rule-router", "creator-aegis-audit"]),
    "characterlock-system": ("deep", "identity and viewpoint locked character workflow", ["creator-seed-incubator", "creator-rule-router", "creator-aegis-audit"]),
    "headlock-system": ("standard", "head and face consistency workflow", ["creator-seed-incubator", "creator-rule-router"]),
    "ai-video-system": ("deep", "shot, scene, motion, and continuity workflow", ["creator-seed-incubator", "creator-aegis-audit"]),
    "prompt-pack": ("tight", "reusable prompts and prompt QA", ["creator-seed-incubator", "creator-skillsmith-factory"]),
    "character-registry": ("deep", "profile IDs, variants, and universe records", ["creator-seed-incubator", "creator-base-workspace"]),
    "content-campaign": ("creative", "launch, content calendar, and platform publishing plan", ["creator-seed-incubator", "creator-paul-loop"]),
    "creator-tooling": ("standard", "scripts, validators, workflow tools, and skill suites", ["creator-seed-incubator", "creator-paul-loop", "creator-skillsmith-factory"]),
    "application": ("deep", "software, app, UI, API, or service", ["creator-seed-incubator", "creator-paul-loop", "creator-aegis-audit"]),
    "workflow": ("standard", "repeatable SOP, skill, or automation", ["creator-seed-incubator", "creator-paul-loop"]),
    "utility": ("tight", "script, checker, converter, or small tool", ["creator-seed-incubator", "creator-paul-loop"]),
    "research-system": ("standard", "repo, toolchain, or source analysis system", ["creator-seed-incubator", "creator-aegis-audit"]),
}


def write_type(type_id: str, rigor: str, purpose: str, skills: list[str]) -> None:
    path = TYPE_ROOT / type_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "guide.md").write_text(
        f"""# {type_id} Guide

## Purpose

{purpose}.

## When To Use

Use this type when the project primarily needs {purpose}.

## Discovery Questions

- What is the intended output?
- Who reviews or uses the output?
- What source materials are available?
- What acceptance criteria prove the result worked?
- What is explicitly out of scope?

## Anti-Patterns

- Starting implementation before acceptance criteria exist.
- Treating non-blocking questions as blockers.
- Expanding the project beyond the selected type without explicit approval.

## Example Output

`PLANNING.md` with typed scope, acceptance criteria, risks, open questions, and handoff target.
""",
        encoding="utf-8",
    )
    (path / "config.md").write_text(
        f"""# {type_id} Config

- rigor: `{rigor}`
- minimum_acceptance_criteria: 3
- recommended_handoff_target: `creator-paul-loop`

## Required Sections

- Goal
- Context
- Scope
- Out of Scope
- Acceptance Criteria
- Risks
- Open Questions
- Handoff Target

## Optional Sections

- Source Assets
- Stakeholders
- Timeline
- Rollback
""",
        encoding="utf-8",
    )
    secondary = "\n".join(f"- `{skill}`" for skill in skills[1:]) or "- none"
    (path / "skill-loadout.md").write_text(
        f"""# {type_id} Skill Loadout

## Primary Skill

`{skills[0]}`

## Secondary Skills

{secondary}

## Rule Domains

- `GLOBAL`
- `{type_id}`

## Audit Domains

- planning quality
- source evidence
- acceptance criteria

## State Surfaces

- `.creator/projects.json`
- `.creator/state.json`
- `.creator/decisions.json`
""",
        encoding="utf-8",
    )


def main() -> int:
    for type_id, (rigor, purpose, skills) in PROJECT_TYPES.items():
        write_type(type_id, rigor, purpose, skills)
    print(f"Materialized {len(PROJECT_TYPES)} SEED project type reference sets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
