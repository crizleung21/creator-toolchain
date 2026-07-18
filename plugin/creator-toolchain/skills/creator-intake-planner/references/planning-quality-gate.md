# Planning Quality Gate

## Required Checks

- [ ] Exact seven-artifact Intake package exists.
- [ ] Project type is selected and matches `project.json`.
- [ ] Required sections are present and non-empty.
- [ ] At least three acceptance criteria use observable Given / When / Then fields.
- [ ] Blocking and non-blocking questions are separated.
- [ ] No blocking questions remain before approval.
- [ ] Scope and out-of-scope boundaries are explicit.
- [ ] Handoff target is `creator-execution-cycle`.
- [ ] Source paths resolve safely or use an explicit `MISSING:` marker.
- [ ] One project ID is preserved across artifacts.
- [ ] No implementation artifact exists in the planning directory.

## Results

- `pass`
- `pass_with_non_blocking_questions`
- `fail_needs_more_planning`

Only the first two results are eligible for explicit approval. A non-blocking question is preserved in the handoff and does not silently become a blocker.
