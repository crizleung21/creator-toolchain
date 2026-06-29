# Creator Workspace State Contract

## Schema

All declared surfaces use `schema_version: 0.3.0` and an explicit `owner_skill`.

## Surfaces

| File | Responsibility | Privacy class |
|---|---|---|
| `workspace.json` | Workspace identity, architecture pointer, state pattern, optional active plan. | `publishable_template` |
| `projects.json` | Registered project state. | `repository_workflow_state` |
| `entities.json` | Reusable creator entities. | `private` |
| `state.json` | Active and blocked project IDs plus health state. | `repository_workflow_state` |
| `session-insights.json` | Reviewable session observations. | `private` |
| `operator.json` | Operator preferences. | `private` |
| `backlog.json` | Deferred work. | `repository_workflow_state` |
| `surfaces.json` | Required state-surface registry. | `publishable_template` |
| `decisions.json` | Current accepted architecture decisions. | `repository_workflow_state` |
| `rules.json` | Active domains, rules, commands, and staged proposals. | `repository_contract` |

## Pointer Rules

- `architecture_map` is required and must resolve to a file.
- `active_plan` may be `null`; otherwise it must resolve to a file.
- Project plan and summary pointers may be `null`; non-null values must resolve.
- Required surface paths must exist.

## Consistency Rules

- Active project IDs must exist in `projects.json`.
- Rule decision references must exist in `decisions.json`.
- `rules.json` is owned by `creator-rule-router`; all other surfaces are owned by `creator-workspace-manager`.
- Every surface must declare the privacy class assigned in the table above.
- Private local overrides are never package content.
