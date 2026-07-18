# Rule Preflight

A Rule Preflight is read-only. It selects only the active rules needed for the current task and exposes what was not loaded.

## Runtime

```bash
python3 scripts/creator_rule_cli.py preflight \
  --root . \
  --text "請用繁體中文審核 creator-toolchain plugin package" \
  --max-rules 8
```

## Selection Order

```text
enabled domain
→ GLOBAL eligibility or domain/trigger match
→ exclusion-pattern check
→ active Rule status
→ severity
→ domain priority
→ deterministic Rule ID order
→ context budget
```

## Output Contract

```md
# Rule Preflight

## Matched Domains

| Domain | Match reason | Rules loaded |
|---|---|---:|

## Selected Rules

| Rule ID | Domain | Severity | Rule | Selection reason |
|---|---|---|---|---|

## Non-Loaded Candidate Rules

| Rule ID | Domain | Reason |
|---|---|---|

## Excluded Domains

| Domain | Reason |
|---|---|

## Conflict Warnings

| Conflict ID | Type | Blocking | Evidence |
|---|---|---:|---|

## Next Action
```

The output must preserve excluded candidates and context-budget omissions. Do not summarize them away.

A blocking relevant conflict means the selected rules cannot be treated as an authoritative automatic policy set until the underlying Rule records are resolved.
