# PLAN-001 — Phase 7 Behavior Harness and Writable Golden E2E

## Status

`IN_PROGRESS`

## Goal

Establish rerunnable behavior evidence and prove the complete writable Creator Toolchain core loop in an isolated repository.

## Scope

- Add formal behavior run and report Schemas.
- Add a pluggable response/evaluator harness.
- Bind required observations to raw-response line spans.
- Preserve prohibited-observation judgments and evaluator confidence.
- Record commit, package payload, catalog hash, harness version, runtime versions, raw response hash, timestamps, and exit code.
- Reject partial runs as release evidence.
- Add freshness detection across commit, package, catalog, and harness changes.
- Add the writable `creator-asset-naming-checker` Golden E2E.
- Run the Golden E2E as an explicit GitHub Actions step and upload its report.

## Golden Chain

```text
fresh repository
→ bootstrap
→ intake and quality gate
→ explicit approval
→ register project
→ execution handoff
→ implement deterministic utility
→ verify byte-identical output
→ mandatory closure
→ apply execution state proposal
→ rule preflight
→ immutable evidence audit
→ final workspace validation and green workspace health
```

## Safety Boundary

This slice does not claim GATE-11 or GATE-12. The historical 34-case report remains stale until a real current runtime and evaluator rerun every catalog case. Fixture adapters used in unit tests validate the harness mechanics only; they are not promoted as product behavior evidence.

## Acceptance Criteria

- Catalog validation rejects duplicate or malformed cases.
- Required observation `PASS` results contain valid response line spans and generated excerpts.
- Out-of-range or unbound evidence is rejected.
- A selected-skill mismatch forces a failed case.
- A filtered run is `INCOMPLETE`.
- Existing run directories are never overwritten.
- Report freshness changes when commit, package, catalog, or harness changes.
- Golden E2E writes and closes a real project, registers final state, performs Rule Preflight and Evidence Audit, and ends with zero workspace validation findings.
- Two isolated Golden E2E runs produce byte-identical utility evidence.

## Remaining Phase 7 Work

- Connect a current Codex response adapter.
- Connect an independent evaluator adapter.
- Rerun all 34 plugin-only and repo-local cases.
- Promote only a complete, passing, current report.
- Update canonical behavior status and repository health to current/green when all gates pass.
