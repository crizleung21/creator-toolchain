# creator-tooling Skill Loadout

## Primary Skill

`creator-intake-planner`

## Secondary Skills

- `creator-execution-cycle`
- `creator-rule-router`
- `creator-evidence-audit`
- `creator-skill-workbench`

## Rule Domains

- `GLOBAL`
- `creator-toolchain`
- `coding`

## Audit Domains

- implementation correctness
- package safety
- test evidence

## State Surfaces

- `.creator/plans/{project_slug}/`
- `.creator/state-proposals/{project_id}.json`
- `.creator/projects.json` through a staged proposal owned by `creator-workspace-manager`

## Handoff

After an explicit `handoff-to-execution` approval, generate `.creator/handoffs/{project_id}.json` for `creator-execution-cycle`.
