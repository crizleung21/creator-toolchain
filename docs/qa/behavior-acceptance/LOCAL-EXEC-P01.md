Assumption: “this accepted plan” refers to the repository’s documented slide-deck fixture; no standalone `PLANNING.md` currently exists.

### Plan

- `PLANNING.md`: scope, bounded tasks, references, slide count, audience, outline, assumptions, BDD criteria, risks, verification steps, exclusions, and execution handoff.
- `PLAN-001.md`: task-to-output mapping derived from the accepted inputs.
- Supporting inputs: `DECISIONS.md`, `OPEN-QUESTIONS.md`, `HANDOFF.md`, and `fixture.md`.

### Execute

Produce one artifact per bounded task:

- `execution/ASSET-ASSUMPTIONS.md`
- `execution/SLIDE-OUTLINE.md`
- `execution/GENERATION-ACCEPTANCE-CRITERIA.md`
- `execution/OPEN-QUESTIONS.md`

Each task record must identify work performed, files changed, deviations, and status. Persistent registries, automatic generation, and Google Slides integration remain excluded.

### Verify

For every task, record:

- Observable BDD criterion result
- Evidence path
- `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`
- Append-only `activity_ledger.jsonl` event

Verification must prove that planning, assumptions, unresolved questions, and execution handoff remain distinct. No separate `VERIFY-001.md` filename is mandated.

### Reconcile

Required closure artifacts:

- `RECONCILIATION-001.md`: planned versus actual work, deviations, concerns, and proposed state changes
- `SUMMARY-001.md`: outcome and verification summary
- `STATE-UPDATE-PROPOSAL-001.json`
- Final append-only ledger event
- One recommended next action

Expected overall status is `DONE_WITH_CONCERNS` because slide count, audience, poses, and real asset paths remain unresolved. The next action is to collect those production inputs.

Contracts: [EXEC-P01.md](/Users/criz/Desktop/creator-toolchain-rebaseline/docs/qa/behavior-acceptance/EXEC-P01.md:1) and [CHAIN-P01.md](/Users/criz/Desktop/creator-toolchain-rebaseline/docs/qa/behavior-acceptance/CHAIN-P01.md:65).