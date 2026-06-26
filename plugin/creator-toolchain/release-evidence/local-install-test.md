# Local Install Test

## Status

Pass with temporary `CODEX_HOME` on 2026-06-26.

## Required Evidence

- plugin appears in local marketplace: pass
- install command succeeds: pass
- plugin appears as installed and enabled: pass
- hooks are absent by scaffold policy: pass
- debug prompt-input exposes all seven skill names: pass
- default prompt manual UI run: optional repeat before public release

## Evidence

`codex plugin add creator-toolchain --marketplace creator-toolchain-local --json` returned:

```json
{
  "pluginId": "creator-toolchain@creator-toolchain-local",
  "name": "creator-toolchain",
  "marketplaceName": "creator-toolchain-local",
  "version": "1.0.0-draft",
  "authPolicy": "ON_INSTALL"
}
```
