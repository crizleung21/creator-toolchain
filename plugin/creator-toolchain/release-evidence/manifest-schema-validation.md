# Manifest Schema Validation

## Status

Pass for local Codex CLI marketplace discovery and install smoke test on 2026-06-26. Re-run before public release.

## Requirement

Before release, validate `plugin/creator-toolchain/.codex-plugin/plugin.json` against the current official schema and record the command, source, date, and result here.

## Current Evidence

- Manifest location: `plugin/creator-toolchain/.codex-plugin/plugin.json`
- Skills location: `plugin/creator-toolchain/skills/`
- Repo-local marketplace: `.agents/plugins/marketplace.json`
- Official reference: https://developers.openai.com/codex/plugins/build
- Schema risk removed: no custom top-level `release_gates` field in manifest.

## CLI Evidence

Executed with temporary `CODEX_HOME` to avoid mutating the user's real Codex config:

```text
codex plugin marketplace add /Users/criz/Desktop/creator-toolchain --json
codex plugin list --available --json
codex plugin add creator-toolchain --marketplace creator-toolchain-local --json
codex plugin list --json
```

Observed:

- marketplace name: `creator-toolchain-local`
- plugin id: `creator-toolchain@creator-toolchain-local`
- version: `1.0.0-draft`
- installed: `true`
- enabled: `true`
