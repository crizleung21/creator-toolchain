# Skill Specification Contract

```yaml
skill_name:
description:
tier: suite|standalone|task-only
primary_trigger:
secondary_triggers: []
not_for: []
inputs: []
outputs: []
modes: []
folders: []
references: []
assets: []
scripts: []
state_surfaces: []
rule_domains: []
acceptance_tests: []
owner:
phase_added:
```

## Requirements

- `skill_name` must be unique and match its directory.
- Description must name an action, trigger context, and boundary.
- Each mode must map to deterministic references, optional assets, and state surfaces.
- Mutable state requires an owner and explicit write boundary.
- Acceptance tests include positive routing, negative routing, resource integrity, and mutation safety.
