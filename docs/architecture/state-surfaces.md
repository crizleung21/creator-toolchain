# Creator Workspace State Surfaces

Generated from `config/surface-registry.json`. Do not maintain a second manual registry.

| Surface ID | Path | Schema | Owner | Privacy | Required | Mutable | Archive |
|---|---|---|---|---|---:|---:|---|
| `workspace` | `.creator/workspace.json` | `schemas/workspace/workspace.schema.json` | `creator-workspace-manager` | `publishable_template` | yes | yes | `retain` |
| `projects` | `.creator/projects.json` | `schemas/workspace/projects.schema.json` | `creator-workspace-manager` | `repository_workflow_state` | yes | yes | `retain` |
| `entities` | `.creator/entities.json` | `schemas/workspace/entities.schema.json` | `creator-workspace-manager` | `private` | yes | yes | `retain` |
| `state` | `.creator/state.json` | `schemas/workspace/state.schema.json` | `creator-workspace-manager` | `repository_workflow_state` | yes | yes | `retain` |
| `session-insights` | `.creator/session-insights.json` | `schemas/workspace/session-insights.schema.json` | `creator-workspace-manager` | `private` | yes | yes | `retain` |
| `operator` | `.creator/operator.json` | `schemas/workspace/operator.schema.json` | `creator-workspace-manager` | `private` | yes | yes | `retain` |
| `backlog` | `.creator/backlog.json` | `schemas/workspace/backlog.schema.json` | `creator-workspace-manager` | `repository_workflow_state` | yes | yes | `retain` |
| `surfaces` | `.creator/surfaces.json` | `schemas/workspace/surfaces.schema.json` | `creator-workspace-manager` | `publishable_template` | yes | yes | `retain` |
| `decisions` | `.creator/decisions.json` | `schemas/workspace/decisions.schema.json` | `creator-workspace-manager` | `repository_workflow_state` | yes | yes | `retain` |
| `rules` | `.creator/rules.json` | `schemas/workspace/rules.schema.json` | `creator-rule-router` | `repository_contract` | yes | yes | `retain` |

## Ownership

- `creator-workspace-manager` owns nine workspace surfaces.
- `creator-rule-router` owns `.creator/rules.json`.
- State changes must be validated, atomic, and evidence-backed.
