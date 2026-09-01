# PLAN-002 — Phase 7 Current Runtime and Independent Evaluator

## Status

`IN_PROGRESS`

## Goal

Execute all 34 canonical Behavior Acceptance cases against a real hosted model runtime and a separate evaluator model, preserve raw responses and evidence spans, and promote only a complete current passing report.

## Runtime

- Provider: GitHub Models REST inference API.
- Authentication: GitHub Actions `GITHUB_TOKEN` with `models: read`.
- Response model: `openai/gpt-4.1-mini`.
- Evaluator model: `openai/gpt-4o-mini`.
- Independence: response and evaluator model IDs must differ.

## Scope

- Add a dependency-free GitHub Models client with bounded retry and rate-limit handling.
- Add real response and evaluator adapters.
- Keep the response model blind to required and prohibited observations.
- Bind evaluator claims to raw-response line spans through the local evaluator.
- Add a dedicated, manually triggerable or trigger-file-gated runtime workflow.
- Execute all 34 cases and upload immutable run evidence.
- Promote only a complete PASS report tied to the tested commit, package payload, catalog, and harness.

## Acceptance Criteria

- All 34 catalog cases execute.
- Response and evaluator use different model IDs.
- Every required PASS has a valid evidence span.
- Every prohibited PRESENT has a valid evidence span.
- Selected skill matches the invoked catalog skill.
- Adapter or model errors remain ERROR evidence and cannot fall back to an old report.
- Canonical report promotion occurs only for 34/34 PASS.
- Repository health becomes green only after current evidence is promoted.

## Safety Boundary

The dedicated runtime workflow has `contents: read` and `models: read`. It cannot push or alter repository state. Evidence promotion remains a separate reviewed commit.
