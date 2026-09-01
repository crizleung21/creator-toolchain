# Recovery Operations

Recovery preserves existing evidence and returns work only through declared lifecycle transitions.

## Supported Recovery Types

```text
orphan-plan
interrupted-execution
failed-verification
blocked-task
state-divergence
scope-creep
incomplete-reconciliation
```

## Run Recovery

```bash
python3 scripts/creator_execution_closure.py recover \
  --root . \
  --project-id PROJECT-ID \
  --type failed-verification \
  --actor operator \
  --reason "The verification artifact did not satisfy the acceptance criterion"
```

## Required Effects

- write or extend `RECOVERY-PLAN.md`;
- create type-specific artifacts such as `BLOCKER.md`, `STATE-DIVERGENCE.md`, or `SCOPE-CREEP.md`;
- append an immutable recovery ledger event;
- preserve prior verification evidence;
- validate the resulting execution documents;
- restore original bytes if validation fails.

## Prohibited Shortcuts

- bypassing task verification;
- editing ledger history;
- mutating workspace state directly;
- jumping to an undeclared lifecycle state;
- claiming `DONE` while closure artifacts are incomplete.
