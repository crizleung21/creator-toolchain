# Rule Context Budget

## Purpose

Rule selection must be task-scoped. Loading every domain increases collision risk and makes exclusions invisible.

## Defaults

- Match only enabled domains.
- Keep `GLOBAL` eligible.
- Match non-GLOBAL domains by exact domain ID or configured trigger keyword.
- Apply domain exclusion patterns before selecting Rules.
- Select active Rules only.
- Rank by severity, domain priority, and Rule ID.
- Default maximum: 8 Rules.
- Report every matching Rule omitted by status or budget.
- Do not load Commands unless the task asks for a Command.
- Do not load long examples or Decision history unless needed for a conflict or governance decision.

## Required Evidence

A preflight records:

- why each domain matched;
- why a candidate was excluded;
- why a Rule was not loaded;
- whether relevant conflicts are blocking or advisory;
- one next action.

`creator-rules:preflight` never mutates `.creator/rules.json`.
