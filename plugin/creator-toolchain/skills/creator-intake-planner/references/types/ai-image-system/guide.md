# ai-image-system Guide

## Purpose

Create a repeatable AI image generation and quality-control pipeline.

## Required Inputs

- visual brief
- reference assets
- model constraints

## Expected Deliverables

- prompt architecture
- generation workflow
- QA rubric

## Observable Acceptance Patterns

- brief is reproducible
- outputs meet visual constraints
- failed generations are classified

## Discovery Questions

- Which required inputs are already available?
- Which deliverables are mandatory for the accepted MVP?
- Which acceptance patterns can be verified deterministically?
- Which risks require explicit guardrails or rollback?
- What is explicitly out of scope?

## Risk Checklist

- style drift
- copyright risk
- non-reproducible parameters

## Example

Campaign key-visual system

## Boundary

Do not implement this project type inside Intake. Produce the canonical planning package, pass the Planning Quality Gate, and require explicit approval.
