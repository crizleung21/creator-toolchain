# Execution Lifecycle Operations

## Entry Requirement

Execution starts only from an explicitly approved Intake handoff. Draft or failed-gate plans cannot execute.

## Initialize

```bash
python3 scripts/creator_execution_lifecycle.py initialize \
  --root . \
  --handoff .creator/handoffs/PROJECT-ID.json \
  --tasks /path/to/tasks.json
```

## Inspect

```bash
python3 scripts/creator_execution_lifecycle.py status \
  --root . \
  --project-id PROJECT-ID
```

## Transition Execution

```bash
python3 scripts/creator_execution_lifecycle.py transition \
  --root . \
  --project-id PROJECT-ID \
  --to VERIFYING \
  --actor operator \
  --reason "Implementation tasks completed"
```

## Transition a Task

```bash
python3 scripts/creator_execution_lifecycle.py task \
  --root . \
  --project-id PROJECT-ID \
  --task-id TASK-ID \
  --to EXECUTED \
  --actor operator \
  --reason "Artifact produced"
```

## Record Verification

```bash
python3 scripts/creator_execution_lifecycle.py verify \
  --root . \
  --project-id PROJECT-ID \
  --task-id TASK-ID \
  --result PASS \
  --actual-result "Expected output observed" \
  --evidence evidence/result.json
```

A task cannot reach terminal completion without an evidence path and SHA-256.

## Close and Reconcile

```bash
python3 scripts/creator_execution_closure.py close \
  --root . \
  --project-id PROJECT-ID \
  --status DONE \
  --actor operator \
  --recommended-next-action "Review the state-update proposal"
```

Closure produces reconciliation, summary, ledger evidence, and a state-update proposal.
