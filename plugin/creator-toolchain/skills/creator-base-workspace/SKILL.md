---
name: creator-base-workspace
description: Manage Creator Toolchain repo-local workspace state, projects, entities, operator profile, PSMM, backlog, custom surfaces, pulse checks, groom cycles, drift score, and surface validation.
---

# creator-base-workspace

Use this skill to inspect and maintain `.creator/` state surfaces.

## Owned Surfaces

- `.creator/workspace.json`
- `.creator/projects.json`
- `.creator/entities.json`
- `.creator/state.json`
- `.creator/psmm.json`
- `.creator/operator.json`
- `.creator/backlog.json`
- `.creator/surfaces.json`
- `.creator/decisions.json`

## Workflows

- `creator-base:surface list`
- `creator-base:surface create`
- `creator-base:surface validate`
- `creator-base:surface archive`
- `creator-base:surface convert`
- `creator-base:pulse`
- `creator-base:groom`

## Guardrails

- `.creator/*.json` is the active state contract.
- Do not require upstream `.base/data/*.json`.
- PSMM may create staged rule proposals, but must not auto-promote rules.
- Do not silently archive or delete state.

See `references/state-surfaces.md`, `references/pulse-groom.md`, and `references/psmm-rule-bridge.md`.
