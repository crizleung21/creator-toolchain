# Execution and Escalation Statuses

| Status | Meaning |
|---|---|
| `PLANNED` | Task or lifecycle work is defined but not authorized for execution. |
| `APPROVED` | The Intake handoff explicitly authorizes execution planning. |
| `EXECUTING` | Accepted tasks are being performed. |
| `VERIFYING` | Executed task outputs are being checked against observable criteria. |
| `RECONCILING` | All tasks are verified and closure is being generated. |
| `DONE` | Closure passed with no residual concerns. |
| `DONE_WITH_CONCERNS` | Closure passed and explicit residual concerns remain. |
| `NEEDS_CONTEXT` | Missing information prevents safe progress. |
| `BLOCKED` | External change, approval, or dependency is required. |
| `RECOVERING` | A named recovery workflow is restoring a valid execution path. |
| `FAILED` | Task verification failed; remediation and re-verification are required. |

Terminal status is never inferred. It requires the mandatory closure artifacts and ledger evidence.
