# PLAN-001 — Phase 1 State Foundation Slice

## Status

`IN_PROGRESS`

## Goal

Begin Phase 1 by adding the deterministic state foundation without migrating the live repository state before migration and rollback gates exist.

## Scope

- Add ten workspace JSON Schemas targeting state schema `0.4.0`.
- Add ten canonical workspace templates.
- Add idempotent workspace bootstrap and read-only check/dry-run modes.
- Add atomic write, optimistic-lock state store, deterministic IDs, and append-only ledger support.
- Add migration planning and backup support while keeping live `--write` migration gated.
- Add unit tests for the new support layer.

## Explicit Boundary

This slice does not modify the repository's live `.creator/*.json` surfaces or the existing validator constant. Live migration remains a later Phase 1 task after fixture, rollback, and cross-file migration tests are complete.

## Acceptance Criteria

- Given a fresh temporary repository, when bootstrap runs, then all ten state surfaces and the architecture pointer are created and validate.
- Given an initialized workspace, when bootstrap runs again, then no existing user state is overwritten.
- Given an atomic write whose post-write validator fails, then the original bytes are restored.
- Given a stale surface hash, when compare-and-swap write is attempted, then the write is rejected.
- Given an append-only ledger, when a duplicate ID or invalid sequence is appended, then the append is rejected.
- Given all new tests, when unit discovery runs, then every test passes.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Next Phase 1 Slice

Implement migration fixtures, live `0.3.0 → 0.4.0` write/rollback, update the repository state and validator, and add schema-aware cross-file validation.
