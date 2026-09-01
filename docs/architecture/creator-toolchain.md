# Creator Toolchain Architecture

## Purpose

Creator Toolchain provides seven Codex Skills that separate routing, planning, execution, state ownership, rule governance, Skill development, and evidence review while sharing deterministic support modules.

## Seven-Skill Architecture

| Skill | Owns |
|---|---|
| `creator-orchestrator` | workflow selection and explicit handoffs |
| `creator-intake-planner` | typed intake and Planning Quality Gate |
| `creator-execution-cycle` | approved execution, verification, reconciliation, and recovery |
| `creator-workspace-manager` | workspace state, Health, maintenance, and reconciliation |
| `creator-rule-router` | contextual rules, proposals, approvals, exclusions, and conflicts |
| `creator-skill-workbench` | Skill discovery, scaffolding, distillation, scoring, and audit |
| `creator-evidence-audit` | evidence-backed findings, remediation guidance, and execution handoffs |

Python support under `scripts/` implements deterministic validation and mutation beneath these owners. It is not an eighth Skill.

## Core Control Flow

```text
BOOTSTRAP
→ INTAKE
→ PLAN QUALITY GATE
→ APPROVAL
→ EXECUTION
→ VERIFICATION
→ RECONCILIATION
→ STATE PROPOSAL
→ OWNER-GATED STATE UPDATE
→ RULE PREFLIGHT
→ HEALTH
→ AUDIT / REMEDIATION HANDOFF
```

## Workflow Boundaries

- Intake does not implement product work.
- Execution requires an explicitly approved handoff.
- Workspace maintenance does not execute backlog work.
- Rule proposals do not auto-promote.
- Evidence Audit does not mutate the reviewed target.
- Every durable mutation is validated, owner-checked, repository-relative, and atomic.

## Deterministic Support Layer

Support modules provide:

- schema `0.4.0` workspace bootstrap and cross-file validation;
- safe path resolution and symlink-escape prevention;
- atomic writes, optimistic locking, backup, and rollback;
- deterministic IDs and append-only ledgers;
- typed intake artifacts and planning gates;
- execution state transitions, verification records, closure, and recovery;
- canonical surface materialization and evidence-derived Health;
- staged rule operations and conflict analysis;
- rerunnable behavior and writable Golden E2E QA;
- version binding, package inventory, reproducible ZIP, clean installation, and release evidence.

## State Model

Ten JSON surfaces under `.creator/` implement schema `0.4.0`. Formal schemas live in `schemas/workspace/`; bootstrap templates live in `templates/workspace/`; the machine-readable canonical registry is owned by `scripts/creator_state_store.py` and materialized by `scripts/materialize_surface_registry.py`.

## Package Model

```text
Authoritative Skills: .agents/skills/
Generated mirror:     plugin/creator-toolchain/skills/
```

The runtime package contains the manifest, README, changelog, MIT license, and generated Skill mirror only. State, development scripts, tests, schemas, and evidence remain repository tooling.

## Release Model

A stable release requires all 18 gates:

- repository, schema, migration, Skill, mirror, and package contracts;
- unit and integration tests;
- writable Golden E2E;
- 34/34 current Behavior Acceptance;
- byte-identical ZIP builds;
- clean installation and exactly seven discovered Skills;
- green Health;
- expected release changes;
- successful final branch and post-merge `main` validation.

## Non-Goals

The stable runtime does not require an eighth Skill, mandatory hooks, MCP servers, SaaS integrations, telemetry, private state, a desktop or web UI, or P2 productization.
