---
name: creator-paul-loop
description: Execute an existing plan through Plan, Apply, Qualify, and Unify with BDD acceptance criteria, verification evidence, recovery workflows, state reconciliation, and final summary. Do not use for raw ideation.
---

# creator-paul-loop

Use this skill only after a plan is accepted.

## Submodes

- `creator-paul:plan`
- `creator-paul:apply`
- `creator-paul:qualify`
- `creator-paul:unify`
- `creator-paul:progress`
- `creator-paul:status`
- `creator-paul:recover`

## Loop

```text
PLAN
→ APPLY
  → EXECUTE TASK
  → QUALIFY TASK
→ UNIFY
→ SUMMARY
→ LEDGER APPEND
→ STATE UPDATE PROPOSAL
```

## Required Closure

Every execution cycle must end with:

- `UNIFY-{seq}.md`
- `SUMMARY-{seq}.md`
- append-only `activity_ledger.jsonl` event
- one recommended next action

## Statuses

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

See `references/plan-apply-qualify-unify.md`.
