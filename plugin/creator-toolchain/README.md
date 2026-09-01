# Creator Toolchain Plugin

Creator Toolchain `v1.1.0` packages seven Codex Skills for creator planning, approved execution, repository-local state, rule governance, Skill development, evidence review, and workflow routing.

## Install

```bash
codex plugin marketplace add crizleung21/creator-toolchain --ref v1.1.0 --json
codex plugin add creator-toolchain@creator-toolchain --json
```

Start a new Codex thread after installation. Do not enable this installed copy together with the repository-local `.agents/skills/` copy.

## Included Skills

```text
creator-orchestrator
creator-intake-planner
creator-execution-cycle
creator-workspace-manager
creator-rule-router
creator-skill-workbench
creator-evidence-audit
```

## Runtime Contents

- `.codex-plugin/plugin.json`
- `skills/`, generated from the authoritative `.agents/skills/` source
- `README.md`
- `CHANGELOG.md`
- `LICENSE`

## Trust Policy

- exactly seven core Skills are packaged;
- hooks, MCP servers, app integrations, telemetry, and private workspace state are not included;
- the generated Skill mirror must remain byte-equivalent to the authoritative source;
- exact package integrity, current Behavior Acceptance, reproducible ZIP, clean installation, and seven-Skill discovery must pass before release.
