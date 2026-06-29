# PLANNING.md — Reusable Character Consistency System

## Goal

Create a repeatable workflow for generating one visually consistent character across an entire slide deck, including varied poses, expressions, framing, and scenes.

## Project Type

`slide-deck`

The deck consumes an AI image consistency workflow; it does not implement a persistent character registry.

## Inputs

- Front, side, and back character references
- Character design notes
- Desired slide count and aspect ratio
- Slide outline or narrative
- Intended audience
- Approved image model and generation tool

## Scope

1. **Character lock sheet**
   - Facial structure, proportions, hair, clothing, palette
   - Immutable traits versus traits allowed to vary
   - Front, profile, rear, and three-quarter views

2. **Prompt system**
   - Fixed identity block reused verbatim
   - Variable pose, expression, camera, scene, and lighting blocks
   - Negative prompt covering common identity drift
   - Model, version, seed, reference strength, and aspect-ratio records

3. **Slide image manifest**
   - Slide number and narrative purpose
   - Pose, expression, framing, gaze, background, and composition
   - Space reserved for slide copy
   - Generation status and selected asset version

4. **Generation workflow**
   - Approve a neutral anchor image
   - Generate required viewpoints
   - Test a small pose and expression matrix
   - Generate slide assets from approved references
   - Correct failures through controlled regeneration or editing
   - Freeze approved assets before deck assembly

5. **Consistency review**
   - Identity and silhouette
   - Hair and wardrobe details
   - Body proportions
   - Style, palette, and rendering
   - Scene continuity
   - Composition suitability for its slide

6. **Versioning**
   - Suggested filename: `character_slide-{NN}_{shot}_{version}.{ext}`
   - Store prompt, model settings, references, and review result with each asset
   - Never overwrite an approved version

## Out of Scope

- Automatic slide generation
- Google Slides integration
- Persistent character or asset registry
- Training a custom model or LoRA
- Multiple-character continuity
- Final image generation during planning

## Acceptance Criteria

- Given approved character references, when images are generated for different slides, then the character retains the defined immutable traits.
- Given a slide requirement, when its manifest entry is reviewed, then pose, expression, framing, background, and text-safe space are specified.
- Given an approved image, when another operator reproduces it, then the recorded prompt and generation settings are sufficient to repeat the workflow.
- Given generated candidates, when the review rubric is applied, then each candidate receives an observable pass, revise, or reject result.
- Given a rejected image, when it is regenerated, then only identified variable blocks change unless the character lock is deliberately revised.

## Risks

- Model updates causing style or identity drift
- Reference overload reducing pose flexibility
- Inconsistent wardrobe details in complex scenes
- Composition conflicts between character placement and slide text
- Seed reuse being mistaken for guaranteed reproducibility

## Open Questions

### Blocking

None. Planning assumes reference images will be available before execution.

### Non-blocking

- Which image model and reference-conditioning features will be used?
- Is the visual style photorealistic, illustrated, or 3D?
- How many slides and unique poses are required?
- Are wardrobe changes permitted?
- What threshold defines acceptable identity consistency?

## Handoff Target

`creator-execution-cycle`

First execution phase: build the character lock sheet, prompt template, slide image manifest, and review rubric; then validate them with three test images before producing the full deck.

## Planning Quality Gate

`pass_with_non_blocking_questions`

The workspace is read-only, so this plan was not persisted as `PLANNING.md`.