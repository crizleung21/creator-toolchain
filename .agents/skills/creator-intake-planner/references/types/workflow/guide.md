# workflow Guide

## Purpose

Define a repeatable SOP or automation.

## Required Inputs

- trigger
- actors
- source materials

## Expected Deliverables

- workflow specification
- state transitions
- verification checklist

## Observable Acceptance Patterns

- same input yields consistent routing
- handoffs are explicit
- failure recovery is defined

## Discovery Questions

- Which required inputs are already available?
- Which deliverables are mandatory for the accepted MVP?
- Which acceptance patterns can be verified deterministically?
- Which risks require explicit guardrails or rollback?
- What is explicitly out of scope?

## Risk Checklist

- implicit ownership
- missing rollback
- scope creep

## Example

AI image review workflow

## Boundary

Do not implement this project type inside Intake. Produce the canonical planning package, pass the Planning Quality Gate, and require explicit approval.
