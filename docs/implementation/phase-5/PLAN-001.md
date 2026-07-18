# PLAN-001 — Phase 5 Rule Governance Foundation

## Status

`IN_PROGRESS`

## Goal

Establish real declared Rule Router domains, deterministic rule mutations, staged approval, immutable decision evidence, semantic conflict audit, and a functioning zh-Hant preflight without changing the packaged Skill before the runtime contracts are verified.

## Scope

- Expand `.creator/rules.json` from two domains to all seven declared domains.
- Add formal domain, rule, command, proposal, decision-entry, and conflict-report Schemas.
- Add `scripts/creator_rule_store.py`.
- Add `scripts/creator_rule_conflicts.py`.
- Support deterministic list, inspect, mutation, proposal, approval, rejection, recall, exclusion, command, decision-search, and preflight operations.
- Require actor and rationale for every direct mutation.
- Stage proposals without applying them.
- Apply proposals only after explicit approval.
- Append immutable decision entries for approvals, rejections, recalls, and direct mutations.
- Block proposal approval when the candidate introduces a blocking conflict.
- Add deterministic Rule Preflight selection with context-budget and exclusion evidence.
- Add focused unit tests.

## Safety Boundary

This slice does not yet modify the authoritative `creator-rule-router` Skill or Plugin mirror. It does not mark historical Behavior evidence current. Skill integration, package regeneration, health integration for unresolved rule conflicts, and final Phase 5 evidence remain for Slice 2.

## Acceptance Criteria

1. Given the live rules surface, when it is validated, then all seven declared domains exist.
2. Given a zh-Hant Plugin packaging task, when preflight runs, then `GLOBAL`, `zh-hant`, and `creator-toolchain` can match without loading every rule.
3. Given a staged proposal, when no approval is recorded, then its payload is not active.
4. Given a valid staged proposal and explicit approval, when approval runs, then the change and one immutable decision entry are written atomically.
5. Given a blocking duplicate, contradiction, unsafe rule, or duplicate command, when approval is attempted, then no candidate change is written.
6. Given a missing actor or duplicate ID, when mutation is attempted, then the rules surface bytes remain unchanged.
7. Given the complete repository suite, when CI runs, then every configured gate passes.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/creator_rule_conflicts.py --root .
python3 scripts/creator_rule_store.py preflight --root . --text "請用繁體中文審核 creator-toolchain plugin package"
python3 scripts/validate_creator_toolchain.py --scope all
```

## Next Slice

Integrate the authoritative Rule Router Skill and Mode-to-Resource Map, complete conflict-resolution and proposal references/assets, connect unresolved conflicts to Workspace Health, regenerate the Plugin mirror and package report, and satisfy all Phase 5 exit gates.
