# Deterministic Workflow Routing

## Source of Truth

`config/workflow-routing.json` defines route IDs, unique priorities, trigger signals, exclusions, required sources, expected artifacts, support scripts, and boundaries.

## Decision Procedure

1. Normalize the request without changing its meaning.
2. Evaluate routes by descending unique priority.
3. Apply `match_all`, `match_any`, and `exclude_any` signals.
4. Select the first matching route or the single declared fallback.
5. Check required sources and support-script availability.
6. Return exactly one primary workflow and all considered-route evidence.
7. Stop at the handoff boundary.

## Ambiguity Rules

- One-skill build, restructure, scaffold, score, or audit takes Workbench precedence.
- Repository, system, package, or multi-surface evidence audit routes to Evidence Audit.
- An approved plan routes to Execution even if the request also mentions implementation.
- State and Rule mutations route to their owning skills.
- A raw idea falls back to Intake.

## Route Decision Contract

```text
route_id
primary_workflow
secondary_workflow
required_sources
expected_artifact
missing_inputs
boundary
handoff_prompt
support_script
support_script_available
matched_signals
considered_routes
```

The route decision is planning evidence. It does not authorize execution or state mutation.
