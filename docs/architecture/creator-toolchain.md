# Creator Toolchain Architecture

## Purpose

Creator Toolchain provides seven Codex skills that separate routing, planning, execution, state, rules, skill development, and evidence review.

## Seven-Skill Architecture

`creator-orchestrator` routes intent. `creator-intake-planner` creates typed plans. `creator-execution-cycle` implements accepted plans. `creator-workspace-manager` owns repository state. `creator-rule-router` governs contextual rules. `creator-skill-workbench` develops skills. `creator-evidence-audit` produces evidence-backed remediation handoffs.

## Workflow Boundaries

Each workflow owns one phase and hands explicit artifacts to the next phase. Planning does not implement; maintenance does not execute backlog work; evidence review does not mutate its target.

## Deterministic Support Layer

The seven skills remain the workflow owners. Python support modules provide deterministic workspace bootstrap, JSON Schema validation, atomic state writes, optimistic locking, append-only ledgers, migration, rollback, and repository validation. These modules are implementation support and do not constitute an eighth skill.

## State Model

Ten JSON surfaces under `.creator/` implement schema `0.4.0`. Formal schemas live in `schemas/workspace/`; canonical bootstrap templates live in `templates/workspace/`. The workspace manifest declares the current architecture and optional active plan.

All state changes require schema validation, ownership checks, safe repository-relative paths, and atomic writes. Multi-file migrations additionally require a checksum backup manifest and byte-equivalent rollback verification.

## Rule Governance

Rules are selected by domain and trigger relevance. New observations remain staged until explicit approval. Rule domains declare scope, owner, update timestamp, rules, commands, exclusions, and decision references.

## Skill Workbench

Skills use progressive disclosure, validated frontmatter, references, assets, collision checks, and measurable acceptance criteria.

## Evidence Review

Evidence review separates immutable findings, remediation guidance, execution handoff, risk, rollback, and verification gates.

## Plugin Package

`.agents/skills/` is authoritative. `plugin/creator-toolchain/skills/` is a byte-equivalent generated mirror. Runtime contents are enforced by an exact package inventory. Workspace state, development scripts, schemas, tests, and migration evidence are repository tooling and are not packaged as private runtime state.

## Validation Gates

Release requires unit tests, schema and cross-file state validation, migration and rollback tests, mirror parity, package integrity, reproducible ZIP output, current behavior acceptance, and clean installation.

## Non-Goals

The runtime package does not include hooks, MCP servers, app integrations, private state, development scripts, tests, or build evidence.
