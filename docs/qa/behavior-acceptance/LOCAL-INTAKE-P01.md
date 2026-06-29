# PLANNING.md — Reusable Character Consistency System

## Goal

Create a repeatable workflow for generating one visually consistent character across a slide deck, including varied poses, expressions, framing, and scenes.

## Project Type

`slide-deck`

The deck consumes an AI image consistency workflow; it does not create a persistent character registry.

## Inputs

- Front, side, and back character references
- Character design notes
- Slide outline, count, and aspect ratio
- Intended audience
- Approved image model and generation tool

## Scope

1. **Character lock sheet**
   - Immutable facial, body, hair, wardrobe, and palette traits
   - Permitted variations
   - Front, profile, rear, and three-quarter views

2. **Prompt system**
   - Fixed identity block
   - Variable pose, expression, camera, scene, and lighting blocks
   - Negative prompt for common identity drift
   - Recorded model, version, seed, reference strength, and aspect ratio

3. **Slide image manifest**
   - Slide purpose and character action
   - Pose, expression, framing, gaze, and background
   - Text-safe space and composition requirements
   - Status and selected asset version

4. **Generation workflow**
   - Approve a neutral anchor image
   - Generate required viewpoints
   - Validate a small pose/expression matrix
   - Generate slide assets from approved references
   - Correct failures through controlled regeneration or editing
   - Freeze approved assets before deck assembly

5. **Consistency review**
   - Identity and silhouette
   - Hair and wardrobe details
   - Body proportions
   - Style, palette, and rendering
   - Scene continuity
   - Slide composition suitability

6. **Versioning**
   - Naming: `character_slide-{NN}_{shot}_{version}.{ext}`
   - Store prompts, settings, references, and review results
   - Never overwrite approved versions

## Out of Scope

- Final image generation during planning
- Automatic slide generation
- Google Slides integration
- Persistent character or asset registry
- Custom-model or LoRA training
- Multiple-character continuity

## Acceptance Criteria

- Given approved references, when images are generated for different slides, then all immutable character traits remain consistent.
- Given a slide requirement, when its manifest entry is reviewed, then pose, expression, framing, background, and text-safe space are specified.
- Given an approved image, when another operator repeats the workflow, then the recorded prompt, references, and settings are sufficient.
- Given generated candidates, when the review rubric is applied, then each receives an observable `pass`, `revise`, or `reject` result.
- Given a rejected candidate, when regenerated, then only identified variable prompt blocks change unless the character lock is deliberately revised.

## Risks

- Model updates introducing identity or style drift
- Reference conditioning restricting pose flexibility
- Wardrobe details changing in complex scenes
- Character placement conflicting with slide text
- Seeds being treated as guaranteed reproducibility

## Open Questions

### Blocking

None. Execution assumes character references will be available.

### Non-blocking

- Which model and reference-conditioning method will be used?
- Is the style photorealistic, illustrated, or 3D?
- How many slides and unique poses are required?
- Are wardrobe changes permitted?
- What measurable threshold defines acceptable identity consistency?

## Handoff Target

`creator-execution-cycle`

First execution phase: create the lock sheet, prompt template, slide manifest, and review rubric, then validate them using three representative test images.

## Planning Quality Gate

`pass_with_non_blocking_questions`

No repository files were changed because the workspace is read-only.