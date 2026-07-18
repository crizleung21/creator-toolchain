# Session Insight Rule Proposal Bridge

```text
Session insight
→ staged rule proposal
→ creator-workspace:maintenance-review
→ creator-rule-router conflict audit
→ explicit approval
→ active rule
```

Workspace Manager may identify and stage a rule proposal, but it must not edit `.creator/rules.json`, resolve semantic conflicts, or promote the proposal. Phase 5 Rule Governance owns validation, conflict handling, approval, rejection, and activation.

Every staged proposal should record:

- source session or insight ID;
- rationale;
- affected domains;
- expected behavior change;
- review or expiry date;
- evidence paths.
