Route decision:

- Primary workflow: `creator-intake-planner`
- Secondary workflow: `creator-execution-cycle`, only after planning approval
- Required source: `fixture.md` plus the three reference images and slide-count/audience values
- Expected artifact: typed `PLANNING.md`, outline, acceptance criteria, open questions, and execution handoff
- Missing inputs: actual images, desired slide count, intended audience
- Do-not-cross boundary: intake cannot edit source, mutate workspace state, create permanent rules, or generate slides. State and rule changes require separately justified workflows.
- Planning gate: observable acceptance criteria, explicit scope, separated blocking questions, and an approved handoff target

No fixture files should be modified. Next prompt: “Create the intake plan for the character image slide deck from `fixture.md`.”