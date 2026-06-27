---
name: creator-seed-incubator
description: Turn raw creator, slide deck, AI image, AI video, character system, prompt pack, content campaign, software, or workflow ideas into a typed PLANNING.md before implementation. Do not use for executing file changes.
---

# creator-seed-incubator

Use this skill for idea intake, typed planning, status, custom project types, graduation, and launch handoff.

## Modes

- `creator-seed:ideate`
- `creator-seed:status`
- `creator-seed:add-type`
- `creator-seed:graduate`
- `creator-seed:launch`

## Core Workflow

```text
idea intake
→ project type selection
→ discovery questions
→ PLANNING.md
→ Planning Quality Gate
→ graduate or launch
```

## Required Artifacts

```text
.creator/plans/{project_slug}/
├── project.json
├── activity_ledger.jsonl
├── SEED-STATE.md
├── PLANNING.md
├── DECISIONS.md
├── OPEN-QUESTIONS.md
└── HANDOFF.md
```

## Planning Quality Gate

Before `graduate` or `launch`, confirm:

- project type selected or custom type defined
- required sections present
- acceptance criteria observable
- blocking questions separated from non-blocking questions
- handoff target selected
- scope boundary explicit

If the gate fails, continue planning or produce `OPEN-QUESTIONS.md`.

See the reference files for project types, graduation, launch, status, and add-type behavior.
