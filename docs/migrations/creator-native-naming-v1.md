# Creator-Native Naming Migration v1

## Policy

This release uses a direct cutover. Previous skill identifiers and command namespaces are not callable aliases. Reload Codex after updating the repo-local checkout or plugin package so skill discovery sees only the current names.

## Skill Mapping

| Previous | Current |
|---|---|
| `creator-seed-incubator` | `creator-intake-planner` |
| `creator-paul-loop` | `creator-execution-cycle` |
| `creator-base-workspace` | `creator-workspace-manager` |
| `creator-skillsmith-factory` | `creator-skill-workbench` |
| `creator-aegis-audit` | `creator-evidence-audit` |

`creator-orchestrator` and `creator-rule-router` retain their names.

## Interface Mapping

| Previous | Current |
|---|---|
| `creator-seed:ideate` | `creator-intake:start` |
| `creator-seed:graduate` | `creator-intake:scaffold` |
| `creator-seed:launch` | `creator-intake:handoff` |
| `creator-paul:apply` | `creator-execution:execute` |
| `creator-paul:qualify` | `creator-execution:verify` |
| `creator-paul:unify` | `creator-execution:reconcile` |
| `creator-base:pulse` | `creator-workspace:health-check` |
| `creator-base:groom` | `creator-workspace:maintenance-review` |
| `SEED-STATE.md` | `INTAKE-STATE.md` |
| `UNIFY-{seq}.md` | `RECONCILIATION-{seq}.md` |
| `.creator/psmm.json` | `.creator/session-insights.json` |

## Preserved History

Source analysis, archived plans, accepted decisions, completed project records, and append-only ledgers retain their original wording. They are provenance, not active interfaces.

## Reload Procedure

1. Disable either the repo-local or plugin copy so both are not active together.
2. Restart or reload Codex skill discovery.
3. Confirm the seven current skills are visible.
4. Replace saved prompts that use previous identifiers with the current mapping above.
