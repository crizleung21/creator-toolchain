# Rule Operations

Use the complete CLI:

```bash
python3 scripts/creator_rule_cli.py --help
```

## Read-Only Operations

```text
list-domains
get-domain
preflight
list-commands
search-decisions
audit-conflicts
```

`audit-conflicts --write` may persist derived evidence at `.creator/rule-conflicts/conflict-report.json`; it does not change active Rules.

## Direct Governed Mutations

```text
create-domain
toggle-domain
add-rule
remove-rule
replace-rule
recall
exclude
add-command
```

Every direct mutation requires:

```text
--actor
--rationale
```

The runtime validates the candidate, audits conflicts, uses optimistic locking, writes atomically, and appends a Decision entry.

## Structured Inputs

Domain, Rule, Command, and Proposal payloads are supplied as JSON files that validate against the formal Schemas.

Example:

```bash
python3 scripts/creator_rule_cli.py add-rule \
  --root . \
  --domain-id coding \
  --rule /tmp/rule.json \
  --actor maintainer \
  --rationale "Require deterministic verification."
```

## No-Write Failure Conditions

- missing actor or rationale;
- duplicate identifier;
- invalid Schema;
- unsupported operation;
- attempt to disable `GLOBAL`;
- unresolved blocking conflict;
- optimistic-lock mismatch;
- invalid affected-domain declaration.

A failed operation must leave `.creator/rules.json` byte-equivalent to its pre-operation state.
