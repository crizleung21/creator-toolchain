# State Registration Proposal

Intake does not own `.creator/projects.json`. After explicit approval it stages:

```text
.creator/state-proposals/{project_id}.json
```

The proposal contains:

- deterministic `PROPOSAL-*` ID;
- operation `register-project`;
- status `staged`;
- target surface `.creator/projects.json`;
- owner `creator-workspace-manager`;
- requested-by `creator-intake-planner`;
- schema-valid project record;
- repository-relative evidence paths;
- creation and update timestamps.

Only `creator-workspace-manager` may review and apply the proposal. Proposal generation must not change `.creator/projects.json` bytes.
