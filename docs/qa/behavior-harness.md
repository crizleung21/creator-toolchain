# Behavior Acceptance Harness

## Purpose

The behavior harness replaces self-declared case results with rerunnable, evidence-bound records. It does not treat an old `PASS` report as current merely because the stored artifact is internally consistent.

## Components

```text
scripts/run_behavior_acceptance.py
scripts/evaluate_behavior_observations.py
schemas/qa/behavior-run.schema.json
schemas/qa/behavior-report.schema.json
```

The runner is adapter-based:

1. a response adapter executes one catalog prompt and returns the selected skill, raw response, Codex version, and model version;
2. an evaluator adapter reviews that raw response and returns line spans for required observations plus absence/presence judgments for prohibited observations;
3. the local evaluator validates every claimed line span against the stored raw response;
4. the runner derives the case result and writes a schema-valid record.

## Response Adapter Contract

The command receives one JSON object on standard input and returns:

```json
{"selected_skill":"creator-orchestrator","response_text":"Raw response text","codex_version":"version","model_version":"model"}
```

A non-zero exit, malformed JSON, empty response, or missing metadata produces an `ERROR` case.

## Evaluator Adapter Contract

The command receives the case, selected skill, and raw response. It returns exact catalog observations, PASS/FAIL or ABSENT/PRESENT results, line spans, and confidence. The local evaluator calculates the excerpt from the declared lines and rejects out-of-range, missing, duplicate, or unknown observation claims.

## Full Run

```bash
python3 scripts/run_behavior_acceptance.py \
  --root . \
  --run-id CURRENT-RUN \
  --response-command "YOUR_RESPONSE_ADAPTER" \
  --evaluator-command "YOUR_EVALUATOR_ADAPTER"
```

A canonical release report requires all 34 catalog cases. A filtered run is marked `INCOMPLETE` even when every selected case passes.

## Freshness

A report is current only when `commit_sha`, `package_payload_sha256`, `catalog_sha256`, and `harness_version` all match. Any mismatch makes the report stale. A failed or incomplete rerun remains evidence and must not be hidden by an older green report.

## Current Phase 7 Boundary

The harness and writable Golden E2E are implemented in the first Phase 7 slice. The historical 34-case report remains `STALE` until an actual current response adapter and evaluator adapter rerun the full catalog.
