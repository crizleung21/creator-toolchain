## Rule Preflight

**Primary workflow:** `creator-rule-router`
**Do-not-cross boundary:** rule selection only; do not plan the deck, generate slides, create registries, or start execution.

### Matched domains

| Domain | Reason |
|---|---|
| `GLOBAL` | Always eligible |
| `slide-deck` | Fixture project type |

### Selected rules

Enabled rules from `GLOBAL` and `slide-deck` would be retrieved and applied before `creator-intake-planner` runs. The fixture does not contain their rule definitions, so no rule IDs can be truthfully listed.

### Non-loaded candidates

All other domains are excluded because they do not match the fixture. Loading every rule is prohibited by the router guardrail against indiscriminate rule loading.

### Conflict warning

The request to load every domain conflicts with that guardrail. In a writable workflow, this boundary decision would be recorded in `.creator/decisions.json`.

### Next action

Route the fixture to `creator-intake-planner`, producing `PLANNING.md`, a slide outline, acceptance criteria, open questions, and an execution-cycle handoff—without implementing Phase 1 exclusions or modifying the fixture.
