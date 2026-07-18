# ai-video-system Guide

## Purpose

Create shot, scene, motion, audio, and continuity workflows for AI video.

## Required Inputs

- story intent
- shot list
- reference media

## Expected Deliverables

- scene specification
- shot prompts
- continuity checks

## Observable Acceptance Patterns

- shot intent is visible
- continuity survives cuts
- motion constraints are respected

## Discovery Questions

- Which required inputs are already available?
- Which deliverables are mandatory for the accepted MVP?
- Which acceptance patterns can be verified deterministically?
- Which risks require explicit guardrails or rollback?
- What is explicitly out of scope?

## Risk Checklist

- temporal drift
- unsafe media
- audio mismatch

## Example

Short-form narrative video pipeline

## Boundary

Do not implement this project type inside Intake. Produce the canonical planning package, pass the Planning Quality Gate, and require explicit approval.
