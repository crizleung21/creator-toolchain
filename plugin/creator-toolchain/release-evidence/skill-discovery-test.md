# Skill Discovery Test

## Expected Skills

- creator-orchestrator
- creator-seed-incubator
- creator-paul-loop
- creator-base-workspace
- creator-rule-router
- creator-skillsmith-factory
- creator-aegis-audit

## Status

Pass for package file discovery, plugin install smoke test, and Codex debug prompt-input exposure on 2026-06-26. Manual UI selection may still be repeated before public release.

## Debug Prompt Input Evidence

Executed with temporary `CODEX_HOME` after installing `creator-toolchain@creator-toolchain-local`:

```text
codex -C /Users/criz/Desktop/creator-toolchain debug prompt-input "Use creator-orchestrator to route this request."
```

Observed all seven skill names in model-visible context:

- `creator-orchestrator`
- `creator-seed-incubator`
- `creator-paul-loop`
- `creator-base-workspace`
- `creator-rule-router`
- `creator-skillsmith-factory`
- `creator-aegis-audit`
