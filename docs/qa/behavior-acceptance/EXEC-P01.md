The accepted fixture requires these lifecycle artifacts:

### Plan

`PLANNING.md` must define:

- Slide-deck scope and bounded tasks
- Required reference images, slide count, and review audience
- Slide outline
- Asset assumptions
- BDD acceptance criteria
- Open questions
- Affected files, risks, and verification steps
- Explicit Phase 1 exclusions
- Handoff to execution

### Execute

Implement tasks individually and record:

- Task performed
- Files or artifacts created/changed
- Deviations from the plan
- Execution status
- No unrelated work, especially character registries, automatic generation, or Google Slides integration

### Verify

For every task, record:

- Observable acceptance-criterion result
- Evidence path
- Status: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`
- Append-only event in `activity_ledger.jsonl`

Verification must prove that planning, asset assumptions, open questions, and implementation handoff are separated.

### Reconcile

Close the cycle with:

- `RECONCILIATION-{seq}.md`: planned versus actual work, deviations, concerns, and proposed state updates
- `SUMMARY-{seq}.md`: concise outcome and verification summary
- Final append-only `activity_ledger.jsonl` event
- One recommended next action

No execution-cycle work is complete until all four closure elements exist.