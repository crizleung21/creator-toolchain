# Creator Workspace State Contract

## Schema

All declared surfaces use `schema_version: 0.4.0`, an explicit `owner_skill`, a canonical `privacy_class`, and ISO-8601 `created_at` / `updated_at` timestamps.

Formal Draft 2020-12 JSON Schemas live under `schemas/workspace/`. Repository validation checks each surface and then enforces cross-file consistency.

## Canonical Surfaces

| File | Responsibility | Privacy class | Owner |
|---|---|---|---|
| `.creator/workspace.json` | workspace identity, architecture pointer, and active plan | `publishable_template` | `creator-workspace-manager` |
| `.creator/projects.json` | registered project state | `repository_workflow_state` | `creator-workspace-manager` |
| `.creator/entities.json` | reusable creator entities | `private` | `creator-workspace-manager` |
| `.creator/state.json` | active/blocked project IDs and Health | `repository_workflow_state` | `creator-workspace-manager` |
| `.creator/session-insights.json` | reviewable session observations | `private` | `creator-workspace-manager` |
| `.creator/operator.json` | operator preferences | `private` | `creator-workspace-manager` |
| `.creator/backlog.json` | deferred work | `repository_workflow_state` | `creator-workspace-manager` |
| `.creator/surfaces.json` | materialized canonical surface registry | `publishable_template` | `creator-workspace-manager` |
| `.creator/decisions.json` | architecture and workflow decisions | `repository_workflow_state` | `creator-workspace-manager` |
| `.creator/rules.json` | domains, rules, commands, proposals, and rule decisions | `repository_contract` | `creator-rule-router` |

This table is explanatory. The machine-readable registry is authoritative and must be checked with:

```bash
python3 scripts/materialize_surface_registry.py --root . --check
```

## Pointer and Reference Rules

- all durable pointers are repository-relative and must remain inside the workspace;
- `architecture_map` is required;
- `active_plan`, project `plan_path`, and `last_summary` may be `null`; non-null paths must resolve;
- active and blocked project IDs must exist in `projects.json`;
- rule decision references must exist in `decisions.json`;
- identifiers must be unique in their declared scope.

## Mutation Protocol

```text
load
→ validate current state
→ verify owner and optimistic-lock preconditions
→ prepare byte-preserving backup
→ transform in memory
→ validate target state
→ write temporary files
→ atomic replace
→ re-read and validate
→ append evidence
→ remove backup
```

Any failure restores the backup and verifies byte equivalence.

## Reconciliation

State changes from Intake, Execution, or Audit are staged as proposals. `creator-workspace-manager` validates ownership, displays a dry-run diff, applies atomically, recalculates Health, and rolls back on failure.

## Migration

Schema `0.3.0` workspaces are migrated with `scripts/migrate_creator_state.py`. See [`docs/migrations/0.3.0-to-0.4.0.md`](../migrations/0.3.0-to-0.4.0.md).

Private local overrides remain excluded from the Plugin package.
