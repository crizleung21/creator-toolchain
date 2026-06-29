Primary workflow: `creator-skill-workbench` for skill design. Runtime handoff: `creator-intake-planner`.

Do-not-cross boundary: `SKILL.md` is the entry point, not a container for all workflow logic and domain knowledge. Guided workflows belong in `references/workflows/`; domain knowledge belongs in `references/frameworks/`; QA belongs in checklists. The intake planner may produce `PLANNING.md`, outline, acceptance criteria, open questions, and an execution handoff, but must not generate slides or registries.

A single-file skill fails the required anatomy and should not be packaged until split appropriately. It must also pass metadata, trigger/boundary, duplicate-name, explicit-state, useful-reference, and acceptance-test checks. No fixture files are modified.