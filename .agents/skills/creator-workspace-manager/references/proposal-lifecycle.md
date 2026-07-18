# Workspace Proposal Lifecycle

## Discovery

Workspace Manager discovers proposals from:

```text
.creator/state-proposals/*.json
.creator/executions/*/state-update-proposal.json
```

```bash
python3 scripts/creator_workspace_proposals.py list --root .
python3 scripts/creator_workspace_proposals.py status --root . --proposal PROPOSAL_PATH
```

The proposal remains immutable with `status: staged`. The effective lifecycle status is derived as:

- `staged`: no receipt exists;
- `applied`: a valid `.creator/reconciliation/{proposal_id}.json` receipt exists;
- `invalid`: schema, ownership, target, duplicate ID, or receipt evidence is inconsistent.

## Preview and Apply

```bash
python3 scripts/reconcile_creator_state.py preview --root . --proposal PROPOSAL_PATH
python3 scripts/reconcile_creator_state.py apply --root . --proposal PROPOSAL_PATH --actor ACTOR
```

Preview is read-only and reports candidate state plus before/after SHA-256 values. Apply requires:

- a supported operation;
- `status: staged`;
- target `.creator/projects.json`;
- owner `creator-workspace-manager`;
- valid evidence;
- a non-empty actor;
- no existing receipt.

Apply writes the state surface, receipt, ledger, and health cache transactionally. Failure restores every touched byte.
