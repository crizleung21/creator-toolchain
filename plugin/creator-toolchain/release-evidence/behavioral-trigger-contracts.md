# Behavioral Trigger Contracts

## Evidence Header

- status: `PASS_STRUCTURAL_MANUAL_MODEL_GATE`
- tested_at: `2026-06-27T15:12:46+0800`
- tested_commit: `ab507f6807b838bf3b4d04a65ac28e45c7e1cd44`
- automated_test: `python3 -m unittest tests.test_skill_contracts -v`
- prompt_catalog: `docs/qa/skill-contract-tests.md`

## Registered Positive and Boundary Contracts

| Skill | Positive trigger | Boundary trigger | Structural result |
|---|---|---|---|
| orchestrator | ambiguous mixed workflow routes to one primary skill | must route rather than execute | PASS |
| SEED | raw idea becomes typed plan | must not modify implementation files | PASS |
| PAUL | accepted plan enters closure loop | must reject unapproved plan/raw ideation | PASS |
| BASE | pulse/groom inspects state | must not silently archive or execute backlog work | PASS |
| CARL | domain preflight selects relevant rules | must not load all rules or auto-promote staging | PASS |
| Skillsmith | discover/scaffold/audit skill | must reject collisions and mega-entry points | PASS |
| AEGIS | evidence-first Layer A/B/C audit | must not apply remediation directly | PASS |

## Automated Evidence

- all seven authoritative `SKILL.md` files expose required workflow and boundary concepts;
- all referenced source and plugin skill trees match;
- all 13 SEED types contain the three required reference files;
- plugin-only and repo-local-only prompt-input discovery expose the correct provenance.

## Manual Model Gate

Model response wording and routing behavior are non-deterministic and are not represented as an automated pass. Before public release, execute the positive and boundary prompts in `docs/qa/skill-contract-tests.md` in the Codex app and record the reviewed outputs. Public publishing remains out of scope for this cycle.
