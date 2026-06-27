# Character Image Slide Project Fixture

This fixture proves that Creator Toolchain can plan a creator-domain workflow without implementing full character registry surfaces in Phase 1.

## Raw Idea

Create a slide deck that organizes character image references, desired poses, visual consistency notes, and generation acceptance criteria.

## Project Type

`slide-deck`

## Inputs

- front reference image
- side reference image
- back reference image
- desired slide count
- intended review audience

## Planned Outputs

- `PLANNING.md`
- slide outline
- acceptance criteria
- open questions
- handoff to `creator-execution-cycle`

## Out of Scope for Phase 1

- persistent character registry
- image asset registry
- automatic slide generation
- external Google Slides integration

## Acceptance Criteria

- Given raw character image slide requirements
- When `creator-intake-planner` plans the project
- Then the output separates planning, asset assumptions, open questions, and implementation handoff
