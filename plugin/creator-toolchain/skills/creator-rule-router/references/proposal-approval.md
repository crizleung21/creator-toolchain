# Proposal and Approval Workflow

## Stage

```bash
python3 scripts/creator_rule_cli.py stage-proposal \
  --root . \
  --operation add-rule \
  --affected-domain coding \
  --payload /tmp/add-rule-payload.json \
  --requested-by creator-workspace-manager \
  --source .creator/session-insights.json \
  --rationale "Repeated correction requires governed review." \
  --expected-behavior-change "Require fresh verification evidence." \
  --review-date 2027-07-18T00:00:00Z
```

Staging:

- validates the proposal contract;
- creates a deterministic Proposal ID;
- stores the payload as inactive evidence;
- does not activate the Rule or Command;
- does not infer user approval.

## Approve

```bash
python3 scripts/creator_rule_cli.py approve-proposal \
  --root . \
  --proposal-id PROPOSAL-ID \
  --actor reviewer \
  --rationale "Approved after conflict review."
```

Approval requires:

- proposal status `staged`;
- non-empty actor and rationale;
- payload and affected domains agree;
- candidate passes Schema validation;
- no unresolved blocking conflict;
- atomic Rule-surface write;
- immutable Decision entry.

The Decision records the Proposal ID and all relevant Conflict IDs.

## Reject

```bash
python3 scripts/creator_rule_cli.py reject-proposal \
  --root . \
  --proposal-id PROPOSAL-ID \
  --actor reviewer \
  --rationale "Redundant with an active Rule."
```

Rejection preserves the proposal and appends Decision evidence. It does not activate the payload.

## Repeated Decisions

An approved or rejected proposal cannot be approved or rejected again. Repeated attempts fail without writes.
