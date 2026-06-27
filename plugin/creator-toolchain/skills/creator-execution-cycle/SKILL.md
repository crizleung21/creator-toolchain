---
name: creator-execution-cycle
description: Execute an existing plan through Plan, Execute, Verify, and Reconcile with BDD acceptance criteria, verification evidence, recovery workflows, state reconciliation, and final summary. Do not use for raw ideation.
---

# creator-execution-cycle

Use this skill only after a plan is accepted.

## Submodes

- `creator-execution:plan`
- `creator-execution:execute`
- `creator-execution:verify`
- `creator-execution:reconcile`
- `creator-execution:progress`
- `creator-execution:status`
- `creator-execution:recover`

## Loop

```text
PLAN
→ EXECUTE
  → EXECUTE TASK
  → VERIFY TASK
→ RECONCILE
→ SUMMARY
→ LEDGER APPEND
→ STATE UPDATE PROPOSAL
```

## Required Closure

Every execution cycle must end with:

- `RECONCILIATION-{seq}.md`
- `SUMMARY-{seq}.md`
- append-only `activity_ledger.jsonl` event
- one recommended next action

## Statuses

- `DONE`
- `DONE_WITH_CONCERNS`
- `NEEDS_CONTEXT`
- `BLOCKED`

See `references/execution-lifecycle.md`.
