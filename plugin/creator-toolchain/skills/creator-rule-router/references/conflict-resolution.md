# Rule Conflict Resolution

## Audit

```bash
python3 scripts/creator_rule_cli.py audit-conflicts \
  --root . \
  --write
```

Conflict types:

| Type | Default effect |
|---|---|
| `duplicate` | blocking |
| `contradiction` | blocking |
| `unsafe_rule` | blocking |
| `duplicate_command` | blocking |
| `scope_overlap` | advisory |
| `stale_rule` | advisory |
| `overbroad_rule` | advisory |
| `stale_decision` | advisory |

## Resolution Model

Conflict Reports are derived. Resolution means changing the underlying governed records, not editing the report.

```text
audit
→ identify affected Rule, Command, Domain, or Decision
→ stage a remediation proposal
→ explicitly approve or reject
→ append Decision with conflict_refs
→ rerun audit
→ regenerate report
→ rerun Workspace Health
```

## Blocking Behavior

- Proposal approval is rejected when the candidate contains a blocking conflict.
- Rule Preflight reports relevant blocking conflicts and does not recommend automatic application.
- Workspace Health emits `RULE_CONFLICT_BLOCKING` as red.
- Advisory conflicts emit `RULE_CONFLICT_ADVISORY` as amber.

## Decision Evidence

Every approved remediation should reference the Conflict IDs it addressed. If no mutation is needed, record a Decision explaining why the conflict is accepted or out of scope, then adjust the governed records or conflict logic through a separate reviewed change.
