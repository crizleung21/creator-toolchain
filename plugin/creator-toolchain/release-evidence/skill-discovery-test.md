# Plugin-Only Skill Discovery Test

## Evidence Header

- status: `PASS`
- tested_at: `2026-06-27T15:12:46+0800`
- tested_commit: `ab507f6807b838bf3b4d04a65ac28e45c7e1cd44`
- environment: fresh temporary `CODEX_HOME`, installed local marketplace, neutral working directory

## Observed Skills

Prompt-input exposed exactly the seven Creator Toolchain plugin skills with plugin provenance:

- `creator-toolchain:creator-orchestrator`
- `creator-toolchain:creator-seed-incubator`
- `creator-toolchain:creator-paul-loop`
- `creator-toolchain:creator-base-workspace`
- `creator-toolchain:creator-rule-router`
- `creator-toolchain:creator-skillsmith-factory`
- `creator-toolchain:creator-aegis-audit`

Every source locator resolved under the temporary plugin cache. No `$REPO_ROOT/.agents/skills` locator appeared because discovery ran from a neutral directory.

## Limitation

This proves installation and model-visible discovery. A manual Codex app selection run remains a pre-public-release UI gate.
