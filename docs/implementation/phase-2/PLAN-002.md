# PLAN-002 — Phase 2 Intake Runtime Integration

## Status

`DONE`

## Goal

Complete Phase 2 by connecting the deterministic Intake contracts to the authoritative Skill and packaged mirror, then implement explicit approval, planning-only scaffolding, execution handoff, staged workspace registration, project-type materialization, and package evidence.

## Scope

- Integrate `creator-intake-planner` modes and Mode-to-Resource Map.
- Add explicit `scaffold-only` and `handoff-to-execution` approval.
- Reject approval when the Planning Quality Gate fails.
- Generate a three-document planning-only scaffold without source code.
- Generate a schema-valid handoff to `creator-execution-cycle`.
- Stage a state-registration proposal owned by `creator-workspace-manager` without changing `.creator/projects.json`.
- Materialize 39 domain-specific type references from the 13-type registry.
- Preserve authoritative/plugin byte parity.
- Regenerate package-integrity evidence.
- Mark historical behavior evidence stale instead of rewriting its package hash.

## Acceptance Criteria

- Given a passing plan and explicit actor, when approval runs, then the selected decision and immutable evidence are recorded.
- Given `scaffold-only` approval, when scaffold runs, then only `PROJECT.md`, `README.md`, and `HANDOFF.md` are generated and execution remains unauthorized.
- Given `handoff-to-execution` approval, when handoff runs, then a schema-valid `.creator/handoffs/{project_id}.json` targets `creator-execution-cycle`.
- Given Intake does not own `.creator/projects.json`, when approval, scaffold, or handoff runs, then a staged registration proposal is generated without mutating that surface.
- Given the project-type registry, when materialization check runs, then all 39 authoritative references match and the plugin mirror is byte-equivalent.
- Given the plugin payload changed, when QA freshness is evaluated, then the old 34-case report is marked `STALE` for the current payload.

## Verification

- full unit-test discovery;
- project-type materialization check;
- skill mirror parity;
- package-integrity report check;
- repository/state/plugin validation;
- reproducible ZIP comparison;
- clean Git diff.

## Rollback

Revert the Phase 2 branch or squash PR. Intake workflows use hidden staging and restore pre-existing outputs when a multi-artifact commit fails.
