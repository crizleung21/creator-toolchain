---
name: creator-rule-router
description: Select, stage, update, audit, recall, exclude, and apply Creator Toolchain domain rules for Codex workflows, including creator production, zh-Hant writing, coding, safety, and project execution.
---

# creator-rule-router

Use this skill before major creator work when domain-specific rules may affect the task.

## Operations

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

## Required Output

Produce a Rule Preflight with matched domains, selected rules, non-loaded candidate rules, conflicts, and next action.

## Guardrails

- `GLOBAL` rules are always eligible but must remain short.
- Do not load all rules by default.
- Excluded matching rules must be recorded with reason.
- Conflicts must create or reference decision log entries.

See `references/rule-preflight.md`.
