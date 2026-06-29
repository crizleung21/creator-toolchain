Primary workflow: `creator-workspace:maintenance-review`.

Do-not-cross boundary: maintenance review may rank backlog items and recommend a next action, but it must not implement features. Implementation requires a handoff to `creator-execution-cycle` after an accepted plan exists.

Against `fixture.md`, execution is `NEEDS_CONTEXT` because:

- No backlog entries or priority evidence identify the highest-priority feature.
- No accepted `PLANNING.md` exists.
- Persistent character and asset registries are explicitly out of scope for Phase 1.

Permitted workflow:

1. Produce a maintenance review identifying review windows, state fixes, rule proposals, and the highest-priority eligible backlog item.
2. Obtain approval for its bounded plan and acceptance criteria.
3. Hand it to `creator-execution-cycle`.
4. Execute and verify one task at a time.
5. Close with `RECONCILIATION-{seq}.md`, `SUMMARY-{seq}.md`, an append-only ledger event, a state-update proposal, and one recommended next action.

No fixture artifact should be modified, archived, deleted, or silently promoted.