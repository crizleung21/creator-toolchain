---
name: creator-skill-workbench
description: Discover, scaffold, distill, score, and audit Codex Skills for Creator Toolchain workflows, including prompt skills, image/video pipeline skills, character system skills, and project execution skills.
---

# creator-skill-workbench

Use this skill to create or audit Codex skills.

## Workflows

- discover
- scaffold
- distill
- score
- audit

## Skill Anatomy

| File Type | Path | Purpose |
|---|---|---|
| Entry Point | `SKILL.md` | metadata and workflow entry |
| Task | `references/workflows/*.md` | guided workflow |
| Framework | `references/frameworks/*.md` | domain knowledge |
| Template | `assets/templates/*.md` | reusable output shape |
| Context | `.creator/context/*.json/md` | mutable context |
| Checklist | `references/checklists/*.md` | QA gate |
| Rules | `.creator/rules.json` | rule routing |

## Required Checks

- `SKILL.md` has `name` and `description`.
- Description has trigger terms and boundary.
- No duplicate skill name.
- References and assets are useful.
- State mutation is explicit.
- Acceptance tests exist.

See `references/skill-spec.md` and `references/compliance-score.md`.
