## Route decision

- Primary workflow: `creator-intake-planner`
- Secondary workflow: `creator-execution-cycle`, only after plan approval
- Product concept: “Character Continuity Review Deck” — a presentation organizing front/side/back references, requested poses, consistency constraints, and image-generation acceptance checks.
- Required source: `fixture.md` plus the three reference images
- Expected planning artifacts: `PLANNING.md`, slide outline, acceptance criteria, `OPEN-QUESTIONS.md`, `HANDOFF.md`, and intake state metadata
- Quality-gate result: `fail_needs_more_planning`

Missing blocking inputs:

- Actual front, side, and back reference images
- Desired slide count
- Intended review audience

The plan would explicitly exclude persistent registries, automatic slide generation, and Google Slides integration.

Do-not-cross boundary: the intake workflow may invent and plan the product, but must not generate slides or begin implementation until the missing inputs are resolved, acceptance criteria are observable, and the plan is approved. Read-only access is not the reason for this boundary.

Next prompt:

> Provide the three reference images, desired slide count, and review audience. Then create and approve the typed `PLANNING.md` before handing it to `creator-execution-cycle` for implementation.