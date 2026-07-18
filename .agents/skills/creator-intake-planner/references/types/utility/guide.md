# utility Guide

## Purpose

Build a focused script, checker, converter, or small tool.

## Required Inputs

- input format
- output format
- error policy

## Expected Deliverables

- executable utility
- fixtures
- usage guide

## Observable Acceptance Patterns

- valid input succeeds
- invalid input is rejected
- output is deterministic

## Discovery Questions

- Which required inputs are already available?
- Which deliverables are mandatory for the accepted MVP?
- Which acceptance patterns can be verified deterministically?
- Which risks require explicit guardrails or rollback?
- What is explicitly out of scope?

## Risk Checklist

- destructive defaults
- path traversal
- ambiguous exit codes

## Example

Duplicate asset detector

## Boundary

Do not implement this project type inside Intake. Produce the canonical planning package, pass the Planning Quality Gate, and require explicit approval.
