# character-registry Guide

## Purpose

Maintain canonical character profiles, variants, relationships, and universe records.

## Required Inputs

- character sources
- naming policy
- variant rules

## Expected Deliverables

- registry schema
- profile records
- validation rules

## Observable Acceptance Patterns

- IDs are unique
- variants reference canonical profiles
- relationships resolve

## Discovery Questions

- Which required inputs are already available?
- Which deliverables are mandatory for the accepted MVP?
- Which acceptance patterns can be verified deterministically?
- Which risks require explicit guardrails or rollback?
- What is explicitly out of scope?

## Risk Checklist

- duplicate identity
- broken references
- private data leakage

## Example

Story universe character registry

## Boundary

Do not implement this project type inside Intake. Produce the canonical planning package, pass the Planning Quality Gate, and require explicit approval.
