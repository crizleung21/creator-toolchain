# Intake Approval Workflow

## Preconditions

- Planning Quality Gate is `pass` or `pass_with_non_blocking_questions`.
- No blocking questions remain.
- An explicit actor supplies one decision: `scaffold-only` or `handoff-to-execution`.
- The project is not already approved or rejected.

## Transaction

1. Copy the canonical plan to a hidden staging directory.
2. Record actor, decision, approval timestamp, and decision ID.
3. Append an immutable entry to `DECISIONS.md`.
4. Update `project.json`, `INTAKE-STATE.md`, and `HANDOFF.md`.
5. Append an approval ledger event.
6. Validate the staged plan.
7. Generate a staged state-registration proposal.
8. Replace the plan and proposal atomically, restoring prior bytes on failure.

Approval never executes the project and never writes `.creator/projects.json`.
