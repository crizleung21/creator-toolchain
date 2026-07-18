# Recovery Workflows

Recovery never bypasses verification, closure, ownership, or ledger requirements.

| Recovery type | Trigger | Allowed result | Required artifacts |
|---|---|---|---|
| `orphan-plan` | `PLAN-001.md` exists but reconciliation is absent | `BLOCKED`, `RECOVERING`, or return to `EXECUTING` through the matrix | `RECOVERY-PLAN.md`, `RECONCILIATION-RECOVERY.md`, and `BLOCKER.md` when blocked |
| `interrupted-execution` | execution stopped while state is `EXECUTING` | `RECOVERING` | `RECOVERY-PLAN.md` |
| `failed-verification` | at least one task is `FAILED` while state is `VERIFYING` | `EXECUTING` | `RECOVERY-PLAN.md`; failed evidence remains preserved |
| `blocked-task` | execution or a task is `BLOCKED` | `RECOVERING` | `RECOVERY-PLAN.md`, `BLOCKER.md` |
| `state-divergence` | repository or workspace evidence differs from the accepted plan | `RECOVERING` or matrix-approved return to execution | `RECOVERY-PLAN.md`, `STATE-DIVERGENCE.md` |
| `scope-creep` | unapproved work is detected | `BLOCKED` | `RECOVERY-PLAN.md`, `SCOPE-CREEP.md`, `BLOCKER.md` |
| `incomplete-reconciliation` | state is `RECONCILING` but closure is incomplete | `RECOVERING` | `RECOVERY-PLAN.md`, `RECONCILIATION-RECOVERY.md` |

## Recovery Record

Every recovery operation records:

- recovery type;
- source and target lifecycle state;
- actor;
- reason;
- timestamp;
- recovery artifact path;
- append-only ledger event.

## Verification Preservation

Failed or prior verification evidence is not deleted. A repaired task must return through the task-state rules and produce new evidence before closure.

## State Boundary

State divergence recovery records evidence for later `creator-workspace-manager` review. It does not run the Phase 4 health engine early and does not write `.creator/projects.json`.
