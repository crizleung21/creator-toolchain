## Compliance score: 14/100 — Non-compliant

The workbench defines 0–39 as “rewrite required.” Score is evidence-based using a 100-point operationalization of its required checks.

| Component | Score | Finding |
|---|---:|---|
| Frontmatter metadata | 12/15 | `name` and `description` exist; name is syntactically reasonable, but description is inadequate. |
| Triggers and boundaries | 0/20 | “Helps creators” identifies neither triggering tasks nor exclusions. |
| Workflow instructions | 2/20 | “Do the task” provides no inputs, procedure, output contract, decision points, or failure handling. |
| Reference integrity | 0/15 | `references/workflow.md` is missing, making the referenced workflow unusable. |
| State mutation | 0/10 | No read/write behavior or state surfaces are declared. |
| Acceptance tests | 0/15 | No observable completion criteria or tests exist. |
| Name uniqueness | 0/5 | Cannot be verified from the inline artifact; no registry/package context was supplied. |
| **Total** | **14/100** | **Non-compliant; rewrite required.** |

## Remediation actions

1. Replace the description with explicit triggers and boundaries, for example: “Guides creators through defining and validating content-production tasks; use for scoped workflow execution, not open-ended ideation.”
2. Replace “Do the task” with concrete inputs, ordered steps, outputs, error handling, and completion criteria.
3. Create `references/workflow.md` with substantive guidance, or remove the reference.
4. Explicitly declare state behavior—even if the skill is read-only.
5. Add acceptance tests covering trigger selection, valid output, missing inputs, and missing references.
6. Check `creator-helper` against all installed skill names before packaging.
7. Prefer the workbench anatomy convention `references/workflows/<workflow>.md` for a task workflow.