# Recovery Plan

## Recovery {sequence}: {recovery_type}

**Project ID:** `{project_id}`  
**From State:** `{from_state}`  
**Target State:** `{target_state}`  
**Actor:** `{actor}`  
**Recorded At:** `{timestamp}`

### Trigger

### Guardrails

- Preserve verification evidence and ledger history.
- Do not bypass task verification.
- Do not apply workspace state directly.
- Return only through an allowed lifecycle transition.
