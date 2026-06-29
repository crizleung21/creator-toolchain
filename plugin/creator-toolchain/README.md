# Creator Toolchain Plugin

This package contains seven Creator Toolchain skills for Codex.

## Install

```bash
codex plugin marketplace add crizleung21/creator-toolchain --ref v1.0.1 --json
codex plugin add creator-toolchain@creator-toolchain --json
```

Start a new thread after installation. Do not enable this installed copy together with the repository's `.agents/skills/` copy.

## Contents

- `.codex-plugin/plugin.json`
- `skills/`, generated from `.agents/skills/`
- `README.md`
- `CHANGELOG.md`
- `LICENSE`

## Trust Policy

- Hooks, MCP servers, and app integrations are not included.
- Private state and build artifacts are prohibited.
- Generated skills must remain byte-equivalent to the authoritative source.
- Exact package integrity and reproducible-build checks must pass before release.
