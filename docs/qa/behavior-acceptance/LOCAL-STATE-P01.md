# Creator Health Check

- Overall health: **Amber**
- Active projects: None declared.
- Blocked projects: None declared.
- Stale plans: None; `active_plan` is null and no project plans exist.
- Structural divergence: **0%** — all 10 registered surfaces exist, parse, and state validation passes.
- Metadata divergence: **33%** — 3 of 9 workspace-manager surfaces have privacy classifications inconsistent with the skill contract: `entities`, `operator`, and `session-insights`.
- Operational divergence: **Non-zero** despite the stored `0 / green` score:
  - Full validation fails because `docs/qa/behavior-acceptance-report.json` is missing.
  - Only 30 of 34 behavior-acceptance artifacts exist.
  - QA work is present but no project or plan records it.
- Last recorded health check: 2026-06-28.

Next maintenance action: run a maintenance review for the unregistered behavior-acceptance work—account for the four missing artifacts (`LOCAL-AUDIT-P01`, `LOCAL-RULE-P01`, `LOCAL-SKILL-P01`, `LOCAL-STATE-P01`) and missing report, then refresh the stored divergence after validation passes.

No `.creator` state was modified.