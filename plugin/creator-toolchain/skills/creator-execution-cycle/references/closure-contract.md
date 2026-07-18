# Execution Closure Contract

Closure is a single rollback-capable transaction from `RECONCILING` to `DONE` or `DONE_WITH_CONCERNS`.

## Preconditions

- lifecycle state is `RECONCILING`;
- every task is `VERIFIED`;
- every task verification status is `PASS`;
- every evidence path is repository-relative and exists;
- every evidence SHA-256 still matches the recorded bytes;
- actor and recommended next action are non-empty.

## Required Outputs

```text
RECONCILIATION-{seq}.json
RECONCILIATION-{seq}.md
SUMMARY-{seq}.md
state-update-proposal.json
activity_ledger.jsonl event
```

The machine-readable reconciliation records planned tasks, actual verified tasks, deviations, concerns, proposal path, final status, and recommended next action.

## Status Rules

- `DONE` rejects residual concerns.
- `DONE_WITH_CONCERNS` requires at least one explicit concern.
- Changed or missing evidence aborts closure with no durable mutation.
- Existing closure artifacts are never overwritten.

## Transaction Boundary

The transaction snapshots execution state, ledger, and every closure path. Any schema, write, hash, or post-write validation failure restores the prior bytes and removes newly created outputs.

## Final Action

The summary contains exactly one recommended next action. Workspace state remains staged for review rather than applied.
