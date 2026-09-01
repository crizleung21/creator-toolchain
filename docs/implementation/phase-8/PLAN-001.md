# PLAN-001 — Phase 8 Release Automation

## Status

`IN_PROGRESS`

## Goal

Implement one authoritative version source, atomic Plugin mirror synchronization, unified release orchestration, clean-install and seven-skill discovery tests, hardened CI, and commit/package-bound release evidence for Creator Toolchain `v1.1.0`.

## Scope

1. Add `VERSION` as the sole authoritative release version.
2. Derive and validate the Plugin manifest version from `VERSION`.
3. Replace destructive mirror sync with temporary-copy, parity-check, atomic-replace, and rollback behavior.
4. Add `scripts/release_creator_toolchain.py` supporting `--check`, `--build`, and `--version`.
5. Add clean-install validation and exact seven-skill discovery.
6. Rerun the canonical 34-case behavior gate after the final package payload changes.
7. Generate release evidence bound to the functional commit, package payload, ZIP digest, and validation results.
8. Harden GitHub Actions and upload failure/release evidence.

## Safety Boundary

No Git tag or GitHub Release is created during this phase. Publication remains blocked until Phase 9 documentation and final reconciliation close all mandatory gates.

## Acceptance Criteria

- `VERSION`, Plugin manifest, package report, release archive name, tests, and release evidence agree on `1.1.0`.
- A failed mirror replacement restores the previous mirror byte-for-byte.
- Two release builds are byte-identical.
- A clean temporary installation validates and discovers exactly seven Skills.
- The complete 34-case behavior report is current for the final package payload.
- The release command passes from a clean checkout and emits machine-readable evidence.
- The latest Phase 8 Head GitHub Actions run succeeds.
