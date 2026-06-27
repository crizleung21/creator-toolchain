# Local Install Test

## Evidence Header

- status: `PASS`
- tested_at: `2026-06-27T21:23:43+0800`
- tested_commit: `11d7e5991a2d0c00d4a392e23b52bc5311ed50f9`
- codex_cli: `0.142.3`
- environment: fresh temporary `CODEX_HOME`
- working_directory: neutral temporary directory for discovery

## Sequence

```text
codex plugin marketplace add $REPO_ROOT --json
codex plugin add creator-toolchain --marketplace creator-toolchain-local --json
codex plugin list --json
codex -C $NEUTRAL_DIR debug prompt-input "Use creator-orchestrator to route this request."
```

All commands exited `0`.

## Observed Install State

```json
{
  "pluginId": "creator-toolchain@creator-toolchain-local",
  "name": "creator-toolchain",
  "marketplaceName": "creator-toolchain-local",
  "version": "1.0.0-draft.1",
  "installed": true,
  "enabled": true,
  "authPolicy": "ON_INSTALL"
}
```

The temporary home and neutral directory were removed after the test. The user's normal Codex configuration was not modified.
