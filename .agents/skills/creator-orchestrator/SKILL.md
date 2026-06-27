---
name: creator-orchestrator
description: Route Creator Toolchain tasks to the correct workflow skill for ideation, planning, implementation, state, rules, skill creation, audit, or plugin packaging. Use when the right workflow is unclear.
---

# creator-orchestrator

Use this skill to decide which Creator Toolchain workflow should handle a request.

## Output Contract

Return:

- primary workflow
- secondary workflow, if needed
- required source files
- expected artifact
- missing inputs
- do-not-cross boundary
- next prompt

## Routing Matrix

| Situation | Route |
|---|---|
| Raw idea or unclear scope | `creator-seed-incubator` |
| Accepted plan ready for work | `creator-paul-loop` |
| Project state, drift, pulse, groom | `creator-base-workspace` |
| Domain rules or instruction recall | `creator-rule-router` |
| Build or audit a skill | `creator-skillsmith-factory` |
| Evidence-first audit | `creator-aegis-audit` |
| Package or release plugin | Phase 5 plugin workflow |

## Guardrails

- Do not execute a full workflow inside the orchestrator.
- Do not silently edit `.creator/*.json`.
- Mark unavailable phase capabilities as backlog candidates when the suite is partially installed.

See `references/workflow-routing.md`.
