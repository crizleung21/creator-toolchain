Primary workflow: `creator-workspace:maintenance-review`.

It may produce a **Creator Maintenance Review** listing stale plans and archive candidates. It must not delete projects automatically: deletion requires explicit confirmation of the identified candidates.

`fixture.md` provides no project-state records proving any project is stale, so no deletion is permitted.

Do-not-cross boundary: maintenance review may recommend deletion; it cannot silently mutate `.creator/*.json` or delete project artifacts.