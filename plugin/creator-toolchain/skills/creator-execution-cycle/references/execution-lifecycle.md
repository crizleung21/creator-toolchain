# Execution Lifecycle

## Entry Gate

Execution begins only from a schema-valid `.creator/handoffs/{project_id}.json` that records:

- `approval_status: approved`;
- `approval_decision: handoff-to-execution`;
- `target_skill: creator-execution-cycle`;
- a passed Planning Quality Gate;
- one stable project ID;
- seven existing Intake artifact paths.

Invalid entry data must fail before `.creator/executions/{project_id}/` exists.

## Canonical States

```text
PLANNED
APPROVED
EXECUTING
VERIFYING
RECONCILING
DONE
DONE_WITH_CONCERNS
NEEDS_CONTEXT
BLOCKED
RECOVERING
```

## Allowed Transitions

| Current | Allowed next |
|---|---|
| `PLANNED` | `APPROVED`, `NEEDS_CONTEXT` |
| `APPROVED` | `EXECUTING`, `BLOCKED` |
| `EXECUTING` | `VERIFYING`, `BLOCKED`, `RECOVERING` |
| `VERIFYING` | `EXECUTING`, `RECONCILING`, `DONE_WITH_CONCERNS`, `BLOCKED` |
| `RECONCILING` | `DONE`, `DONE_WITH_CONCERNS`, `RECOVERING` |
| `BLOCKED` | `RECOVERING`, `NEEDS_CONTEXT` |
| `RECOVERING` | `EXECUTING`, `VERIFYING`, `RECONCILING`, `BLOCKED` |
| `DONE` | none |
| `DONE_WITH_CONCERNS` | none |
| `NEEDS_CONTEXT` | none |

An unlisted transition fails before state, ledger, or recovery files change.

## Task States

```text
PLANNED
EXECUTING
EXECUTED
VERIFIED
FAILED
BLOCKED
```

Allowed task transitions:

```text
PLANNED   → EXECUTING | BLOCKED
EXECUTING → EXECUTED | BLOCKED
FAILED    → EXECUTING | BLOCKED
BLOCKED   → EXECUTING
```

Verification changes `EXECUTED` to `VERIFIED` or `FAILED`. Task transitions require lifecycle state `EXECUTING`; verification requires lifecycle state `VERIFYING`.

## Phase Rules

### PLAN

Create deterministic task IDs, acceptance criteria, affected-file boundaries, verification methods, and expected results from the accepted handoff.

### EXECUTE

Run one accepted task at a time. Record every task transition in `activity_ledger.jsonl`. Unplanned work is scope creep.

### VERIFY

Require a real repository-relative evidence file. Record the observed result and SHA-256. Do not infer success from intention or prose.

### RECONCILE

Enter only when every task is `VERIFIED`. Rehash evidence, compare planned and actual tasks, record deviations and concerns, and stage the workspace state proposal.

### CLOSE

Create all mandatory closure artifacts transactionally. `DONE` requires no concerns; `DONE_WITH_CONCERNS` requires explicit residual concerns.

## Read-only Status

Status and progress operations may read execution state, tasks, ledger count, and artifact pointers. They must not append events or modify bytes.
