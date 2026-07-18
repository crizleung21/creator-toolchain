# Execution Handoff Workflow

`creator-intake:handoff` requires:

- a passing Planning Quality Gate;
- explicit `handoff-to-execution` approval;
- a preserved canonical project ID;
- no unresolved blocking questions.

## Output

```text
.creator/handoffs/{project_id}.json
```

The handoff records the source plan, target skill `creator-execution-cycle`, gate result, approval evidence, all canonical artifact paths, remaining non-blocking questions, and generation timestamp.

## Boundary

The handoff authorizes the next workflow; it does not execute the plan. Reject duplicate or conflicting handoffs and never infer approval from prose.
