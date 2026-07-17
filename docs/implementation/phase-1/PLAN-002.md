# PLAN-002 — Phase 1 Slice 2

## Goal

Complete the state-schema migration boundary by enabling transactional `0.3.0 → 0.4.0` writes, byte-equivalent rollback, migration fixtures, live repository state conversion, and schema-aware Validator integration.

## Tasks

| Task | Acceptance | Verification | Status |
|---|---|---|---|
| Add dependency-free schema instance validator | Required Schema subset evaluates instances deterministically | Unit tests | `DONE` |
| Add cross-surface validation | Ten formal Schemas plus registry, pointer, ID, and decision references validate | State tests | `DONE` |
| Enable transactional migration | In-memory transform, backup manifest, atomic writes, post-write validation | Migration tests | `DONE` |
| Implement byte-equivalent rollback | Explicit and automatic rollback restore all original bytes | Failure-injection tests | `DONE` |
| Add current `0.3.0` fixtures | Fixture represents all ten pre-migration surfaces | Migration fixture tests | `DONE` |
| Upgrade live state | All ten repository surfaces use `0.4.0` and validate | Repository validator | `DONE` |
| Integrate Validator | `validate_creator_toolchain.py --scope state` consumes formal Schemas and cross-file rules | GitHub Actions run `29599614902` | `DONE` |

## Safety Boundary

- Existing records are preserved.
- No plugin skill or runtime package file is changed.
- The migration backup is not committed because it contains pre-migration private state; checksums and source blob identities are recorded as evidence instead.
- Rollback behavior is tested against repository-equivalent fixtures.

## Rollback

Revert the Slice 2 commits, or run `migrate_creator_state.py --rollback` with the generated backup before merge.

## Completion

`DONE`

GitHub Actions run `29599614902` passed all configured gates. Phase 1 — State Schema `0.4.0` and Deterministic Foundation is complete.
