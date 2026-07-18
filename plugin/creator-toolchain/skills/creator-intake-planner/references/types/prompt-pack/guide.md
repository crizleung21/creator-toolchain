# prompt-pack Guide

## Purpose

Build reusable prompts with variables, examples, and QA criteria.

## Required Inputs

- target task
- model constraints
- example inputs

## Expected Deliverables

- prompt templates
- variable schema
- test cases

## Observable Acceptance Patterns

- variables are explicit
- examples cover edge cases
- outputs can be evaluated

## Discovery Questions

- Which required inputs are already available?
- Which deliverables are mandatory for the accepted MVP?
- Which acceptance patterns can be verified deterministically?
- Which risks require explicit guardrails or rollback?
- What is explicitly out of scope?

## Risk Checklist

- prompt ambiguity
- unsafe instructions
- model-specific assumptions

## Example

AI portrait prompt pack

## Boundary

Do not implement this project type inside Intake. Produce the canonical planning package, pass the Planning Quality Gate, and require explicit approval.
