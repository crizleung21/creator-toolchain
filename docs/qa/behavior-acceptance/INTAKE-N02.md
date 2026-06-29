Primary workflow: `creator-intake-planner` (`creator-intake:start`).

Do-not-cross boundary: no source edits, slide generation, registries, or Google Slides integration during intake.

Current result: `fail_needs_more_planning`. The workflow would produce the planning artifact set, including `PLANNING.md`, `OPEN-QUESTIONS.md`, and `HANDOFF.md`. It must first resolve or classify the missing reference images, slide count, review audience, consistency requirements, and observable acceptance criteria.

After the gate passes, `HANDOFF.md` routes implementation to `creator-execution-cycle`. No fixture files were modified.