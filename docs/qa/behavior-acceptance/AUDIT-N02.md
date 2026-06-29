Primary workflow: `creator-evidence-audit`. Boundary: audit and remediation planning only—no fixture mutation or execution.

The request is rejected: suspected issues cannot be marked critical without evidence.

- Phase 0: Scope the `fixture.md` planning workflow and severity risks.
- Phase 1: Inventory fixture claims, outputs, exclusions, and acceptance criteria.
- Phase 2: Review each suspected issue against cited fixture evidence.
- Phase 3: Compare claimed behavior with available artifact behavior.
- Phase 4: Challenge unsupported severity assumptions.
- Phase 5: Record findings with evidence and limitations.
- Phase 6: Convert substantiated findings into remediation guidance.
- Phase 7: Define change risks, guardrails, and verification gates.
- Phase 8: Prepare an execution handoff only; execution requires approval and `creator-execution-cycle`.

For every suspected issue:

- Observation: What the fixture explicitly shows.
- Interpretation: What that evidence may mean.
- Judgment: Severity proportional to demonstrated impact; otherwise “unverified.”
- Confidence: Stated explicitly.
- Disagreement handling: Preserve contrary interpretations and missing evidence.
- Remediation: Recommend evidence collection before prioritization.

No critical finding is warranted from `fixture.md` merely because an issue is suspected.