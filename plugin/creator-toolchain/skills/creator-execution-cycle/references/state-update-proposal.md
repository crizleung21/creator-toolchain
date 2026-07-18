# Execution State Update Proposal

`creator-execution-cycle` does not own `.creator/projects.json`.

At closure it stages:

```text
.creator/executions/{project_id}/state-update-proposal.json
```

## Required Contract

```text
operation: update-project-execution
status: staged
target_surface: .creator/projects.json
owner_skill: creator-workspace-manager
requested_by: creator-execution-cycle
project_id
execution_status
source_execution
reconciliation_record
reconciliation_markdown
summary
verified_tasks with evidence hashes
concerns
recommended_next_action
created_at
updated_at
```

The proposal must conform to `schemas/execution/state-update-proposal.schema.json`.

## Ownership

Only `creator-workspace-manager` may review and apply the proposal during Workspace Reconciliation. Execution may generate, validate, and reference the proposal, but it must not alter the target surface directly.
