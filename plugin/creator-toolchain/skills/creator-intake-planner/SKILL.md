---
name: creator-intake-planner
description: Turn raw creator, slide deck, AI image, AI video, character system, prompt pack, content campaign, software, or workflow ideas into a typed PLANNING.md before implementation. Do not use for executing file changes.
---

# creator-intake-planner

Use this skill for idea intake, typed planning, status, custom project types, scaffolding, and execution handoff.

## Modes

- `creator-intake:start`
- `creator-intake:status`
- `creator-intake:add-type`
- `creator-intake:scaffold`
- `creator-intake:handoff`

## Core Workflow

```text
idea intake
→ project type selection
→ discovery questions
→ PLANNING.md
→ Planning Quality Gate
→ scaffold or handoff
```

## Required Artifacts

```text
.creator/plans/{project_slug}/
├── project.json
├── activity_ledger.jsonl
├── INTAKE-STATE.md
├── PLANNING.md
├── DECISIONS.md
├── OPEN-QUESTIONS.md
└── HANDOFF.md
```

## Planning Quality Gate

Before `scaffold` or `handoff`, confirm:

- project type selected or custom type defined
- required sections present
- acceptance criteria observable
- blocking questions separated from non-blocking questions
- handoff target selected
- scope boundary explicit

If the gate fails, continue planning or produce `OPEN-QUESTIONS.md`.

See the reference files for project types, scaffolding, handoff, status, and add-type behavior.
