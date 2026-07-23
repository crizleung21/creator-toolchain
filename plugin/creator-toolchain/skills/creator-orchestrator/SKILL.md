---
name: creator-orchestrator
description: Route Creator Toolchain requests to exactly one primary workflow, preserve explicit handoffs and ownership boundaries, and coordinate deterministic Plugin release scripts when the requested capability exists. Use when workflow selection is unclear; do not execute the routed workflow.
---

# creator-orchestrator

Use this skill to select the narrowest Creator Toolchain workflow that can produce the requested artifact without crossing another skill's boundary.

## Modes

- `creator-route:decide`
- `creator-route:handoff`
- `creator-route:release`
- `creator-route:status`

## Deterministic Routing

Repository-local routing uses:

```bash
python3 scripts/creator_workflow_router.py \
  --root . \
  --request "REQUEST" \
  --source "AVAILABLE SOURCE"
```

`config/workflow-routing.json` is the precedence source. A valid decision contains exactly one `primary_workflow`, all considered routes, missing inputs, the ownership boundary, and one handoff prompt.

## Routing Precedence

| Request | Primary workflow |
|---|---|
| Plugin release or publication | `creator-orchestrator` coordinating deterministic release scripts |
| Explicitly approved plan or execution handoff | `creator-execution-cycle` |
| Workspace state, health, reconciliation, maintenance, or archive | `creator-workspace-manager` |
| Rule preflight, mutation, proposal, or conflict audit | `creator-rule-router` |
| Build, restructure, scaffold, score, or audit one skill | `creator-skill-workbench` |
| Evidence-first repository, system, or package audit | `creator-evidence-audit` |
| Raw idea or unmatched request | `creator-intake-planner` |

A request to audit a single skill belongs to Workbench. A repository or package audit belongs to Evidence Audit.

## Release Routing

Release requests no longer target an undefined phase workflow. They remain with this orchestrator and require:

- approved release scope;
- current package-integrity evidence;
- `scripts/release_creator_toolchain.py`;
- all release gates required by the active implementation plan.

Until the Phase 8 release script exists, report the missing capability and stop before ad hoc packaging.

## Output Contract

Return:

- route ID;
- primary workflow;
- optional secondary workflow;
- required sources and missing inputs;
- expected artifact;
- support script and availability;
- do-not-cross boundary;
- deterministic handoff prompt.

## Mode-to-Resource Map

| Mode | Required references | Optional assets | State surfaces |
|---|---|---|---|
| decide | `references/workflow-routing.md` | `assets/route-decision-template.json` | read request context only |
| handoff | `references/workflow-routing.md` | `assets/route-decision-template.json` | no state mutation |
| release | `references/release-routing.md`, `references/workflow-routing.md` | `assets/route-decision-template.json` | read package and release evidence only |
| status | `references/workflow-routing.md` | none | read-only capability inspection |

## Acceptance Tests

- exactly one primary workflow is selected;
- single-skill and system-audit requests are unambiguous;
- release requests resolve to a named deterministic support script;
- missing support scripts are reported rather than invented;
- the orchestrator never mutates `.creator/` state or executes product work.

## Guardrails

- Do not execute the selected workflow inside the orchestrator.
- Do not combine planning and implementation.
- Do not silently mutate `.creator/*.json` or another skill's artifacts.
- Do not invent an undefined phase workflow.
- Do not package or publish a Plugin when release support or evidence is missing.
- Preserve one primary workflow even when secondary consultation is useful.

See `references/workflow-routing.md` and `references/release-routing.md`.
