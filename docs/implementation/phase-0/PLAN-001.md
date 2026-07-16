# PLAN-001 — Phase 0 Baseline Freeze and Contract Lock

## Goal

Add the approved implementation plan to the repository, freeze the exact pre-implementation baseline, preserve the seven-skill invariant, and record the approved schema `0.4.0` architecture decision without changing runtime behavior.

## Source

- Approved plan: `IMPLEMENTATION__PLAN.md`
- Base branch: `main`
- Base commit: `337468cc36e5b4b5b18fc4ec4b129264e3c3c2f5`
- Execution branch: `agent/phase-0-baseline-freeze`

## Tasks

| Task | Acceptance | Verification | Status |
|---|---|---|---|
| `P0-0001` Record baseline | Commit, package, plugin, schema, and QA identifiers recorded | Review `docs/implementation/BASELINE.md` | `DONE` |
| `P0-0002` Create implementation branch | Work is isolated from `main` | Branch exists as `agent/phase-0-baseline-freeze` | `DONE` |
| `P0-0003` Confirm seven skills | Exactly seven names recorded from authoritative sync contract | Review Baseline and source `SKILLS` tuple | `DONE` |
| `P0-0004` Freeze behavior fixtures | Catalog/report IDs and stored result recorded | Parse `BEHAVIOR_BASELINE.json` | `DONE` |
| `P0-0005` Record architecture decision | Accepted `DEC-004` exists | Parse `.creator/decisions.json` | `DONE` |
| `P0-0006` Lock invariants and non-goals | Seven-skill and Phase 0 boundaries are explicit | Review Baseline and implementation plan | `DONE` |

## Acceptance Criteria

### AC-1 — Approved plan is stored without modification

- Given the approved local `IMPLEMENTATION__PLAN.md`
- When it is added to the implementation branch
- Then its Git blob SHA must equal the locally calculated Git blob SHA `f3f5fdf1462d87441cc4514d91e4230a20da4fb6`.

### AC-2 — Baseline is complete

- Given the pre-change repository state
- When Phase 0 is reconciled
- Then the source commit, plugin version, state schema, package payload, QA catalog/report, and seven-skill list are recorded.

### AC-3 — Runtime behavior is unchanged

- Given Phase 0 is a contract-lock phase
- When branch changes are compared with `main`
- Then changes are limited to the approved plan, implementation evidence, and the architecture decision record.

## Risks

- GitHub Actions evidence is unavailable until the Draft PR triggers CI.
- Remote Connector writes create multiple small commits rather than one local atomic commit.
- Phase 0 does not rerun the 34 behavior cases; it freezes the stored evidence only.

## Rollback

Close the Draft PR or revert all branch commits. No runtime package or skill mirror rollback is required because Phase 0 does not modify them.
