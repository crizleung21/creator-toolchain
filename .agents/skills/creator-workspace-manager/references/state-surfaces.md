# Canonical State Surfaces

`config/surface-registry.json` is the single machine-readable registry. `.creator/surfaces.json`, `templates/workspace/surfaces.json`, and `docs/architecture/state-surfaces.md` are generated outputs and must not be maintained independently.

## Canonical Root Surfaces

| Path | Owner | Privacy |
|---|---|---|
| `.creator/workspace.json` | `creator-workspace-manager` | `publishable_template` |
| `.creator/projects.json` | `creator-workspace-manager` | `repository_workflow_state` |
| `.creator/entities.json` | `creator-workspace-manager` | `private` |
| `.creator/state.json` | `creator-workspace-manager` | `repository_workflow_state` |
| `.creator/session-insights.json` | `creator-workspace-manager` | `private` |
| `.creator/operator.json` | `creator-workspace-manager` | `private` |
| `.creator/backlog.json` | `creator-workspace-manager` | `repository_workflow_state` |
| `.creator/surfaces.json` | `creator-workspace-manager` | `publishable_template` |
| `.creator/decisions.json` | `creator-workspace-manager` | `repository_workflow_state` |
| `.creator/rules.json` | `creator-rule-router` | `repository_contract` |

## Commands

```bash
python3 scripts/creator_surface_registry.py list --root .
python3 scripts/creator_surface_registry.py get --root . --path .creator/projects.json
python3 scripts/creator_surface_registry.py validate --root .
python3 scripts/materialize_surface_registry.py --root . --check
```

Root surfaces are required and cannot be archived. Custom or generated non-root artifacts must not be added to the canonical root registry.
