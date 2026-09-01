# Troubleshooting

| Symptom | Likely cause | Corrective action |
|---|---|---|
| `Plugin mirror differs` | authoritative Skills changed without regeneration | run `python3 scripts/sync_plugin_skills.py --write`, then `--check` |
| stale package report | Plugin README, changelog, manifest, or Skill bytes changed | regenerate `docs/qa/package-integrity-report.json` and rerun Behavior Acceptance |
| Behavior status is `STALE` | commit, payload, catalog, or harness changed | run the complete 34-case gate and promote new evidence |
| Health is amber/red | unresolved schema, pointer, rule, evidence, or package signal | inspect `.creator/health/health-report.json` and remediate each signal |
| bootstrap refuses a path | path traversal, symlink escape, or invalid existing JSON | correct the target path or state; do not bypass safety checks |
| lifecycle transition rejected | current state does not allow the requested transition | inspect execution status and use a declared transition or recovery |
| task verification rejected | task is not `EXECUTED` or evidence is missing | produce repository-relative evidence and retry verification |
| reconciliation rejected | wrong owner, invalid proposal, or stale state | preview the proposal, refresh state, and retry through `creator-workspace-manager` |
| rule proposal cannot approve | conflict, missing actor, duplicate ID, or unsafe candidate | resolve conflict and create a new immutable approval decision |
| ZIPs differ | nondeterministic package bytes or build metadata | inspect package file changes; do not release until builds are byte-identical |
| clean install discovers the wrong Skills | unexpected/missing Skill directory or frontmatter mismatch | restore exactly seven generated Skills and rerun package validation |
| GitHub Release workflow skips | `v1.1.0` already exists | inspect the existing Release and assets; do not overwrite silently |

## Diagnostic Command Set

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/materialize_surface_registry.py --root . --check
python3 scripts/materialize_project_type_refs.py --root . --check
python3 scripts/sync_plugin_skills.py --check
python3 scripts/package_integrity.py \
  --root . \
  --package-root plugin/creator-toolchain \
  --check docs/qa/package-integrity-report.json
python3 scripts/validate_creator_toolchain.py --scope all
python3 scripts/release_creator_toolchain.py \
  --root . \
  --check \
  --commit-sha "$(git rev-parse HEAD)"
```
