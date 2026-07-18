# PLAN-002 — Phase 5 Rule Router Integration and Health Signals

## Status

`IN_PROGRESS`

## Goal

Complete Phase 5 by integrating the authoritative Rule Router Skill with the deterministic Rule runtime, exposing every declared governance operation, converting live Rule conflicts into Workspace Health signals, and refreshing Plugin and package evidence.

## Scope

- Replace the Rule Router entry contract with a complete Mode-to-Resource Map.
- Add proposal, approval, conflict-resolution, operation, Schema, preflight, and context-budget references.
- Add proposal, Decision, Conflict Report, and Rule Preflight assets.
- Add a complete Rule Governance CLI for every declared operation.
- Persist derived Conflict Reports without changing active Rules.
- Add red Health signals for blocking conflicts and amber signals for advisories.
- Regenerate the Plugin mirror.
- Refresh package-integrity and Behavior freshness evidence.
- Recalculate the live Workspace Health Report.
- Record final Phase 5 reconciliation and CI evidence.

## Constraints

- `.creator/rules.json` remains exclusively owned by `creator-rule-router`.
- Staged proposals remain inactive.
- Blocking conflicts prevent approval and automatic Rule application.
- Conflict Reports are derived and cannot be edited to claim resolution.
- Workspace Health audits current Rule bytes rather than trusting a stored report.
- No eighth core Skill is added.
- Historical Behavior evidence remains stale until Phase 7.

## Acceptance Criteria

1. Every Rule Router operation is represented in the Skill and complete CLI.
2. The Skill includes deterministic resource discovery for preflight, mutation, proposal, approval, conflict audit, and Decision search.
3. A persisted Conflict Report does not mutate `.creator/rules.json`.
4. A blocking Rule conflict produces red Workspace Health.
5. An advisory Rule conflict produces amber Workspace Health.
6. Proposal approval Decisions include relevant advisory Conflict IDs.
7. Authoritative and Plugin Rule Router trees are byte-equivalent.
8. Exact package inventory and payload evidence match the final branch.
9. Behavior freshness references the final package payload and remains `STALE`.
10. The final full Repository CI run passes.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/sync_plugin_skills.py --check
python3 scripts/package_integrity.py \
  --root . \
  --package-root plugin/creator-toolchain \
  --check docs/qa/package-integrity-report.json
python3 scripts/validate_creator_toolchain.py --scope all
python3 scripts/build_plugin_package.py --root . --output /tmp/build-a.zip
python3 scripts/build_plugin_package.py --root . --output /tmp/build-b.zip
cmp /tmp/build-a.zip /tmp/build-b.zip
```

## Next Phase

After Phase 5 is complete, begin Phase 6 — Routing, Progressive Disclosure, Workbench, and Audit.
