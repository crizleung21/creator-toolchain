---
name: creator-execution-cycle
description: Execute only schema-valid, explicitly approved creator plans through deterministic lifecycle and task transitions, evidence-backed verification, mandatory reconciliation and summary closure, staged workspace state proposals, and explicit recovery workflows. Do not use for raw ideation or unapproved work.
---

# creator-execution-cycle

Use this skill only after `creator-intake-planner` has produced a valid `.creator/handoffs/{project_id}.json` with `approval_status: approved` and `approval_decision: handoff-to-execution`.

## Modes

- `creator-execution:plan`
- `creator-execution:execute`
- `creator-execution:verify`
- `creator-execution:reconcile`
- `creator-execution:progress`
- `creator-execution:status`
- `creator-execution:recover`

## Required Entry Gate

Before creating an execution workspace, verify:

- the handoff conforms to `schemas/project/execution-handoff.schema.json`;
- `target_skill` is `creator-execution-cycle`;
- the source plan and all seven Intake artifacts exist;
- the Planning Quality Gate passed;
- explicit handoff approval exists;
- every path is repository-relative and remains inside the workspace.

An invalid or unapproved handoff produces no execution workspace and no durable mutation.

## Canonical Execution Workspace

```text
.creator/executions/{project_id}/
├── execution-state.json
├── tasks.json
├── PLAN-001.md
├── activity_ledger.jsonl
├── BLOCKER.md                         # when blocked
├── RECOVERY-PLAN.md                   # when recovery starts
├── RECONCILIATION-RECOVERY.md         # orphan or incomplete closure
├── STATE-DIVERGENCE.md                # state divergence evidence
├── SCOPE-CREEP.md                     # unapproved scope evidence
├── RECONCILIATION-{seq}.json
├── RECONCILIATION-{seq}.md
├── SUMMARY-{seq}.md
└── state-update-proposal.json
```

## Canonical Lifecycle

```text
PLAN → EXECUTE → VERIFY → RECONCILE → CLOSE

PLANNED
→ APPROVED
→ EXECUTING
→ VERIFYING
→ RECONCILING
→ DONE | DONE_WITH_CONCERNS
```

The full transition matrix, escalation paths, and task-state rules are defined in `references/execution-lifecycle.md`.

## Deterministic Operations

Repository-local execution uses:

```bash
python3 scripts/creator_execution_lifecycle.py initialize \
  --root . \
  --handoff .creator/handoffs/PROJECT-ID.json \
  --tasks TASKS.json

python3 scripts/creator_execution_lifecycle.py transition \
  --root . \
  --project-id PROJECT-ID \
  --to EXECUTING \
  --actor ACTOR \
  --reason "Begin accepted tasks"

python3 scripts/creator_execution_lifecycle.py task \
  --root . \
  --project-id PROJECT-ID \
  --task-id TASK-ID \
  --to EXECUTED \
  --actor ACTOR \
  --reason "Task output completed"

python3 scripts/creator_execution_lifecycle.py verify \
  --root . \
  --project-id PROJECT-ID \
  --task-id TASK-ID \
  --result PASS \
  --actual-result "Observed result" \
  --evidence evidence/task.txt

python3 scripts/creator_execution_closure.py close \
  --root . \
  --project-id PROJECT-ID \
  --status DONE \
  --actor ACTOR \
  --recommended-next-action "Ask creator-workspace-manager to review the staged proposal"

python3 scripts/creator_execution_closure.py recover \
  --root . \
  --project-id PROJECT-ID \
  --type failed-verification \
  --actor ACTOR \
  --reason "Repair the failed task and rerun verification"
```

Plugin-only use follows the same contracts using packaged assets and references. Never invent approval, evidence, task completion, or workspace state application.

## Verification Evidence Contract

Every task records:

```text
task_id
acceptance_criteria
verification.method
verification.command
verification.expected_result
verification.actual_result
verification.evidence_path
verification.evidence_hash
verification.status
verification.verified_at
status
```

A `PASS` requires a real repository-relative evidence file. Closure rehashes every evidence file and rejects stale or changed evidence without mutation.

## Mandatory Closure

A cycle cannot enter `DONE` or `DONE_WITH_CONCERNS` until every task is `VERIFIED` and the transaction creates:

- `RECONCILIATION-{seq}.json`;
- `RECONCILIATION-{seq}.md`;
- `SUMMARY-{seq}.md`;
- `state-update-proposal.json`;
- an append-only reconciliation ledger event;
- one non-empty recommended next action.

`DONE` rejects residual concerns. `DONE_WITH_CONCERNS` requires at least one explicit concern.

## State Mutation Boundary

`creator-execution-cycle` stages `state-update-proposal.json` for `.creator/projects.json`; it does not apply workspace state. The proposal owner and reviewer is `creator-workspace-manager`.

## Recovery Workflows

Supported recovery types:

- `orphan-plan`;
- `interrupted-execution`;
- `failed-verification`;
- `blocked-task`;
- `state-divergence`;
- `scope-creep`;
- `incomplete-reconciliation`.

Every recovery records an allowed lifecycle transition, appends ledger evidence, preserves prior verification records, and creates the required recovery artifact. See `references/recovery-workflows.md`.

## Mode-to-Resource Map

| Mode | Required references | Optional assets | State surfaces |
|---|---|---|---|
| plan | `references/execution-lifecycle.md`, `references/acceptance-driven-work.md` | `assets/plan-template.md`, `assets/ledger-event-template.json` | approved handoff; `.creator/executions/{project_id}/` |
| execute | `references/execution-lifecycle.md`, `references/in-session-context-policy.md` | `assets/decision-template.md` | `execution-state.json`, `tasks.json`, ledger |
| verify | `references/acceptance-driven-work.md`, `references/execution-lifecycle.md` | none | `tasks.json`, evidence files, ledger |
| reconcile | `references/closure-contract.md`, `references/state-update-proposal.md` | `assets/reconciliation-template.md`, `assets/summary-template.md`, `assets/state-update-proposal-template.json` | execution closure artifacts; staged proposal |
| progress | `references/execution-lifecycle.md` | none | read-only execution workspace |
| status | `references/execution-lifecycle.md`, `references/escalation-statuses.md` | none | read-only execution workspace |
| recover | `references/recovery-workflows.md`, `references/escalation-statuses.md` | `assets/blocker-template.md`, `assets/recovery-plan-template.md`, `assets/reconciliation-recovery-template.md` | execution state, recovery artifacts, ledger |

## Guardrails

- Do not execute raw ideas or unapproved plans.
- Do not bypass the lifecycle transition matrix.
- Do not mark a task verified without current evidence and SHA-256.
- Do not close while any task is unverified or failed.
- Do not overwrite closure artifacts.
- Do not silently expand scope.
- Do not apply `.creator/projects.json` or another skill-owned surface directly.
- Preserve the project ID, task IDs, history sequence, and append-only ledger.
- Return exactly one recommended next action at closure.

See `references/execution-lifecycle.md`, `references/acceptance-driven-work.md`, `references/closure-contract.md`, `references/state-update-proposal.md`, `references/recovery-workflows.md`, `references/escalation-statuses.md`, and `references/in-session-context-policy.md`.
