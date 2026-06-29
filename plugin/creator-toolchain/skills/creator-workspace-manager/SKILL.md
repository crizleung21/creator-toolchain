---
name: creator-workspace-manager
description: Manage Creator Toolchain repo-local workspace state, projects, entities, operator profile, Session Insights, backlog, custom surfaces, health checks, maintenance reviews, state divergence, and surface validation.
---

# creator-workspace-manager

Use this skill to inspect and maintain `.creator/` state surfaces.

## Owned Surfaces

- `.creator/workspace.json`
- `.creator/projects.json`
- `.creator/entities.json`
- `.creator/state.json`
- `.creator/session-insights.json`
- `.creator/operator.json`
- `.creator/backlog.json`
- `.creator/surfaces.json`
- `.creator/decisions.json`

## Workflows

- `creator-workspace:surface list`
- `creator-workspace:surface create`
- `creator-workspace:surface validate`
- `creator-workspace:surface archive`
- `creator-workspace:surface convert`
- `creator-workspace:health-check`
- `creator-workspace:maintenance-review`

## Guardrails

- `.creator/*.json` is the active state contract.
- Session Insights may create staged rule proposals, but must not auto-promote rules.
- Do not silently archive or delete state.

See `references/state-surfaces.md`, `references/health-maintenance.md`, and `references/session-insight-rule-bridge.md`.
