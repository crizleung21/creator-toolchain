# Creator Workspace State Contract

## Schema

All declared surfaces use `schema_version: 0.4.0`, an explicit `owner_skill`, a canonical `privacy_class`, and ISO-8601 `created_at` / `updated_at` timestamps.

Formal Draft 2020-12 JSON Schemas live under `schemas/workspace/`. `scripts/validate_creator_toolchain.py --scope state` validates every surface against its schema and then applies cross-file consistency checks.

## Surfaces

| File | Responsibility | Privacy class | Owner |
|---|---|---|---|
| `workspace.json` | Workspace identity, architecture pointer, state pattern, optional active plan. | `publishable_template` | `creator-workspace-manager` |
| `projects.json` | Registered project state. | `repository_workflow_state` | `creator-workspace-manager` |
| `entities.json` | Reusable creator entities. | `private` | `creator-workspace-manager` |
| `state.json` | Active and blocked project IDs plus health state. | `repository_workflow_state` | `creator-workspace-manager` |
| `session-insights.json` | Reviewable session observations. | `private` | `creator-workspace-manager` |
| `operator.json` | Operator preferences. | `private` | `creator-workspace-manager` |
| `backlog.json` | Deferred work. | `repository_workflow_state` | `creator-workspace-manager` |
| `surfaces.json` | Canonical ten-surface registry. | `publishable_template` | `creator-workspace-manager` |
| `decisions.json` | Current architecture decisions. | `repository_workflow_state` | `creator-workspace-manager` |
| `rules.json` | Active domains, rules, commands, staged proposals, and decision log. | `repository_contract` | `creator-rule-router` |

## Surface Registry

Every `surfaces.json` record must exactly declare:

- `surface_id`;
- repository-relative `path`;
- formal `schema` path;
- `owner_skill`;
- `privacy_class`;
- `required`;
- `mutable`;
- `archive_policy`.

The registry must contain exactly the ten required surfaces and must match the canonical registry in `scripts/creator_state_store.py`.

## Pointer and Reference Rules

- `architecture_map` is required and must resolve inside the repository.
- `active_plan` may be `null`; otherwise it must resolve inside the repository.
- Project `plan_path` and `last_summary` may be `null`; non-null values must resolve.
- Active and blocked project IDs must exist in `projects.json`.
- Rule decision references must exist in `decisions.json`.
- Domain, rule, command, project, entity, insight, backlog, and decision identifiers must be unique within their declared scope.

## Mutation Contract

State writes must use deterministic support modules:

```text
validate current state
→ create checksum manifest and byte-preserving backup
→ transform all ten surfaces in memory
→ pre-commit schema and cross-file validation
→ atomic per-file replacement
→ post-write repository validation
→ retain backup for explicit rollback
```

Any migration failure restores every state file from the backup and verifies byte equivalence.

## Migration

Schema `0.3.0` workspaces are migrated with `scripts/migrate_creator_state.py`. See `docs/migrations/0.3.0-to-0.4.0.md`.

Private local overrides remain excluded from the plugin package.
