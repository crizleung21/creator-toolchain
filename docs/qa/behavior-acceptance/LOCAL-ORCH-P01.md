Route Decision

- Primary workflow: `creator-intake-planner`
- Secondary workflow: `creator-execution-cycle`, only after plan approval
- Required source files: Rough idea and any existing character references, prompts, schemas, or workflow notes
- Expected artifact: Typed `PLANNING.md` for the reusable character consistency system
- Missing inputs: Target media, consistency requirements, reference assets, supported tools/models, and acceptance criteria
- Planning-only boundary: Define scope, architecture, artifacts, risks, and BDD acceptance criteria. Do not implement files, prompts, scripts, state changes, or integrations.
- Later handoff: Once `PLANNING.md` is explicitly approved, invoke `creator-execution-cycle` to Plan, Execute, Verify, and Reconcile the implementation.

Handoff prompt:

> Use `creator-intake-planner` to turn this rough reusable character consistency system idea into a typed `PLANNING.md`. Remain planning-only and prepare clear acceptance criteria for a later `creator-execution-cycle` handoff after approval.