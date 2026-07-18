# headlock-system Guide

## Purpose

Preserve head, face, hair, and expression identity.

## Required Inputs

- face references
- angle coverage
- expression range

## Expected Deliverables

- head identity sheet
- prompt constraints
- comparison checklist

## Observable Acceptance Patterns

- landmarks remain consistent
- angles are covered
- expression does not change identity

## Discovery Questions

- Which required inputs are already available?
- Which deliverables are mandatory for the accepted MVP?
- Which acceptance patterns can be verified deterministically?
- Which risks require explicit guardrails or rollback?
- What is explicitly out of scope?

## Risk Checklist

- facial drift
- insufficient angle evidence
- overfitting one image

## Example

Portrait head consistency pack

## Boundary

Do not implement this project type inside Intake. Produce the canonical planning package, pass the Planning Quality Gate, and require explicit approval.
