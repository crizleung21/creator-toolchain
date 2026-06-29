# Recovery Workflows

| Recovery | Trigger | Action |
|---|---|---|
| Orphan Plan Recovery | PLAN exists but no reconciliation | generate `RECONCILIATION-RECOVERY.md` |
| Failed Qualify Recovery | task verification fails | return to Apply or create remediation plan |
| Blocked Task Recovery | status is `BLOCKED` | write `BLOCKER.md` and request missing context |
| State Divergence Recovery | plan and state disagree | run `creator-workspace:health-check` |
| Scope Creep Recovery | unplanned work detected | pause and ask for explicit scope expansion |
