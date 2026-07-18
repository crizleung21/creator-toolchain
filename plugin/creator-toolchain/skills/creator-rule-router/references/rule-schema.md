# Rule Governance Schemas

The active Rule surface is `.creator/rules.json` with state schema `0.4.0`.

Formal Schemas:

```text
schemas/workspace/rules.schema.json
schemas/rules/domain.schema.json
schemas/rules/rule.schema.json
schemas/rules/command.schema.json
schemas/rules/proposal.schema.json
schemas/rules/decision-entry.schema.json
schemas/rules/conflict-report.schema.json
```

## Domain

Required fields:

```text
domain_id
enabled
priority
scope
trigger_keywords
rules
commands
exclude_patterns
decision_refs
owner
updated_at
```

`owner` must be `creator-rule-router`.

## Rule

Required governance metadata:

```text
rule_id
severity
text
status
scope
source
created_at
updated_at
review_date
```

Rule status is one of:

```text
active
disabled
deprecated
```

## Command

Commands declare:

```text
command_id
trigger
workflow
status
source
created_at
updated_at
```

## Proposal

A proposal is stored in `staged_proposals` and includes the operation, inactive payload, requester, source, rationale, affected domains, expected behavior change, review date, timestamps, and approval fields.

Proposal status is:

```text
staged
approved
rejected
```

The payload does not become active while status is `staged`.

## Decision Entry

Approval, rejection, recall, exclusion, and direct governed mutation append an immutable Decision entry containing actor, timestamp, rationale, changes, affected domains, and relevant conflict IDs.

## Conflict Report

Conflict reports are derived evidence. The canonical stored report path is:

```text
.creator/rule-conflicts/conflict-report.json
```

A report may be regenerated at any time from the current Rule bytes and must not be edited to simulate resolution.
