# PLAN-001 — Phase 3 Execution Lifecycle Foundation

## Status

`IN_PROGRESS`

## Goal

Establish the deterministic execution lifecycle beneath `creator-execution-cycle` before adding full reconciliation and recovery closure.

## Scope

- Add the canonical execution states and allowed transition matrix.
- Require a schema-valid, explicitly approved Intake execution handoff.
- Create a transactional execution workspace under `.creator/executions/{project_id}/`.
- Add task lifecycle enforcement and evidence-backed verification.
- Reject illegal transitions without changing state, tasks, or ledger bytes.
- Prohibit `DONE` and `DONE_WITH_CONCERNS` until closure artifacts exist.
- Add formal execution, task, and reconciliation Schemas.
- Add isolated lifecycle and negative-path tests.

## Out of Scope for Slice 1

- Authoritative Skill and plugin mirror integration.
- Final reconciliation and summary generation.
- State-update proposal generation.
- Complete recovery workflows and closure.
- Product implementation execution.

## Acceptance Criteria

1. Given a valid `handoff-to-execution` artifact, when initialization runs, then an `APPROVED` execution workspace is created transactionally.
2. Given an unapproved or malformed handoff, when initialization runs, then no execution directory is created.
3. Given an illegal lifecycle transition, when it is requested, then all durable bytes remain unchanged.
4. Given an executed task, when verification records a real evidence file, then the task becomes `VERIFIED` with a computed SHA-256.
5. Given missing verification evidence, when verification is attempted, then the task and ledger remain unchanged.
6. Given no reconciliation, summary, or state-update proposal, when terminal completion is requested, then the transition is rejected.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Next Slice

Integrate the authoritative Execution Skill, implement closure artifacts and recovery workflows, regenerate the plugin mirror and package report, and satisfy all Phase 3 exit gates.
