---
name: creator-rule-router
description: Select, preflight, stage, approve, reject, recall, exclude, and audit Creator Toolchain rules across GLOBAL, creator-toolchain, zh-Hant, coding, safety, creator-production, and project-execution domains. Use for rule governance and task-scoped rule selection; do not auto-promote proposals or load every rule.
---

# creator-rule-router

Use this skill when a task needs domain-specific rules, a Rule Preflight, a governed Rule mutation, proposal review, Decision lookup, or conflict audit.

## Ownership

`creator-rule-router` exclusively owns `.creator/rules.json`.

Other skills may stage a proposal or request a preflight, but they must not activate, reject, recall, or rewrite Rule records directly.

## Supported Operations

- `creator-rules:list-domains`
- `creator-rules:get-domain`
- `creator-rules:create-domain`
- `creator-rules:toggle-domain`
- `creator-rules:add-rule`
- `creator-rules:remove-rule`
- `creator-rules:replace-rule`
- `creator-rules:stage-proposal`
- `creator-rules:approve-proposal`
- `creator-rules:reject-proposal`
- `creator-rules:recall`
- `creator-rules:exclude`
- `creator-rules:list-commands`
- `creator-rules:add-command`
- `creator-rules:search-decisions`
- `creator-rules:audit-conflicts`

Deterministic command support is provided by:

```bash
python3 scripts/creator_rule_cli.py --help
```

## Mode-to-Resource Map

| Mode | Required references | Optional assets | State surfaces |
|---|---|---|---|
| Preflight | `references/rule-preflight.md`, `references/context-budget.md` | `assets/rule-preflight-template.md` | Read `.creator/rules.json` |
| Inspect domains or commands | `references/rule-schema.md`, `references/rule-operations.md` | none | Read `.creator/rules.json` |
| Direct governed mutation | `references/rule-operations.md`, `references/conflict-resolution.md` | `assets/rule-decision-template.json` | Atomic write `.creator/rules.json` |
| Stage proposal | `references/proposal-approval.md`, `references/rule-schema.md` | `assets/rule-proposal-template.json` | Atomic write `.creator/rules.json`; payload remains inactive |
| Approve or reject | `references/proposal-approval.md`, `references/conflict-resolution.md` | `assets/rule-decision-template.json` | Atomic write `.creator/rules.json` after conflict gate |
| Conflict audit | `references/conflict-resolution.md`, `references/rule-schema.md` | `assets/conflict-report-template.json` | Read `.creator/rules.json`; optionally write derived `.creator/rule-conflicts/conflict-report.json` |
| Decision search | `references/proposal-approval.md` | `assets/rule-decision-template.json` | Read `.creator/rules.json` decision log |

## Governance Lifecycle

```text
task text
→ match enabled domains
→ apply exclusions
→ select active rules within context budget
→ report non-loaded candidates
→ audit relevant conflicts
→ use selected rules only when no blocking conflict applies
```

Rule change lifecycle:

```text
request
→ stage proposal
→ validate payload
→ conflict audit
→ explicit approval or rejection
→ immutable Decision entry
→ atomic Rule-surface write
→ rerun conflict audit and workspace health
```

A staged proposal is evidence, not an active Rule. Never infer approval from prose, recency, urgency, or repeated user behavior.

## Required Rule Preflight Output

Produce:

1. matched domains and match reasons;
2. selected active rules;
3. non-loaded candidate rules and reasons;
4. excluded domains or rules;
5. relevant blocking and advisory conflicts;
6. one recommended next action.

`GLOBAL` is always eligible, but its rules remain bounded by the context budget.

## Conflict Policy

Blocking conflict types:

- duplicate;
- contradiction;
- unsafe rule;
- duplicate command.

Advisory conflict types:

- scope overlap;
- stale rule;
- overbroad rule;
- stale decision.

Blocking conflicts prevent automatic application and proposal approval. Resolve them by changing or rejecting the underlying Rule proposal, then rerun the audit. Do not manually edit a derived Conflict Report to claim resolution.

## Guardrails

- Do not load every domain or every Rule by default.
- Do not auto-promote Session Insights or proposals.
- Require actor and rationale for direct mutation, approval, rejection, recall, or exclusion.
- Reject duplicate Rule, Command, Proposal, Domain, and Decision IDs.
- Preserve rejected, recalled, and superseded governance evidence.
- Keep Decision entries append-only.
- Record excluded matching candidates and conflict IDs.
- Let Workspace Health report unresolved blocking conflicts as red and advisories as amber.
- Never mutate state owned by another skill.

See `references/rule-preflight.md`, `references/context-budget.md`, `references/rule-schema.md`, `references/rule-operations.md`, `references/proposal-approval.md`, and `references/conflict-resolution.md`.
