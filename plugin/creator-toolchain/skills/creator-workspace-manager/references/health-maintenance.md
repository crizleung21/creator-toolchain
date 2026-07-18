# Health and Maintenance

## Evidence-Derived Health

Health is recalculated from the current workspace and repository evidence. Stored values in `.creator/state.json` are a cache, not the source of truth.

Signals include:

- schema, owner, privacy, pointer, and cross-file failures;
- stale plans;
- orphan or unregistered executions;
- terminal executions missing closure;
- stale behavior evidence;
- plugin mirror mismatch;
- package-integrity drift.

```bash
python3 scripts/creator_health_check.py --root .
python3 scripts/creator_health_check.py --root . --write
```

`--write` transactionally updates `.creator/health/health-report.json` and the health cache in `.creator/state.json`.

## Maintenance Review

Maintenance review is read-only:

```bash
python3 scripts/creator_workspace_maintenance.py review --root .
```

It reports health, staged/applied/invalid proposal counts, archive candidates, state fixes, staged rule proposals, and one recommended next action. It must not implement backlog work, mutate state, archive files, or promote rules.
