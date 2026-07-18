# PLAN-002 — Phase 3 Closure, Recovery, and Skill Integration

## Status

`IN_PROGRESS`

## Goal

Complete Phase 3 by making evidence-backed closure, recovery, authoritative Skill behavior, plugin packaging, and QA evidence deterministic and reviewable.

## Scope

- Add a rollback-capable closure transaction from `RECONCILING` to `DONE` or `DONE_WITH_CONCERNS`.
- Revalidate every task evidence file and SHA-256 at closure.
- Generate machine-readable and Markdown reconciliation artifacts, summary, staged state-update proposal, and final ledger evidence.
- Preserve the `creator-workspace-manager` ownership boundary for `.creator/projects.json`.
- Implement orphan-plan, interrupted-execution, failed-verification, blocked-task, state-divergence, scope-creep, and incomplete-reconciliation recovery.
- Integrate the complete lifecycle into the authoritative `creator-execution-cycle` Skill.
- Regenerate the byte-equivalent plugin mirror and exact package-integrity report.
- Mark historical behavior evidence stale for the changed package payload rather than relabelling it current.

## Acceptance Criteria

1. Given all tasks have current `PASS` evidence, when closure runs from `RECONCILING`, then every mandatory closure artifact and one ledger event are created transactionally.
2. Given an evidence file changed after verification, when closure runs, then closure fails and every execution byte remains unchanged.
3. Given `DONE`, when residual concerns are supplied, then closure is rejected; given `DONE_WITH_CONCERNS`, at least one concern is required.
4. Given any supported recovery trigger, when recovery runs, then it uses an allowed lifecycle transition and writes the required recovery evidence without deleting earlier verification history.
5. Given execution closure, when state reconciliation is requested, then only a staged proposal owned by `creator-workspace-manager` is created and `.creator/projects.json` is not mutated.
6. Given the authoritative Execution Skill changes, when mirror and package checks run, then mirror parity and exact package integrity pass.
7. Given the package payload changes, when QA freshness is evaluated, then the earlier 34-case report remains `STALE` until the Phase 7 rerun.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/materialize_project_type_refs.py --root . --check
python3 scripts/sync_plugin_skills.py --check
python3 scripts/package_integrity.py --root . --package-root plugin/creator-toolchain --check docs/qa/package-integrity-report.json
python3 scripts/validate_creator_toolchain.py --scope all
python3 scripts/build_plugin_package.py --root . --output /tmp/build-a.zip
python3 scripts/build_plugin_package.py --root . --output /tmp/build-b.zip
cmp /tmp/build-a.zip /tmp/build-b.zip
git diff --exit-code
```

## Rollback

Revert the Slice 2 commits. Runtime writes snapshot all affected files and restore prior bytes when closure or recovery validation fails.
