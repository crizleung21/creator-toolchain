# Acceptance-Driven Work

Use observable BDD-style criteria:

```md
### AC-1: {Criterion}

- Given {precondition}
- When {action}
- Then {observable result}
```

Each execution task carries one or more acceptance criteria and a verification contract:

```text
method
command or null
expected_result
actual_result
evidence_path
evidence_hash
status
verified_at
```

Acceptance may be proven by file existence, command output, rendered artifact, runtime behavior, or explicit review evidence. A claimed result without a real evidence file is not verification.

Closure rehashes the evidence file. Changed evidence invalidates closure until verification is rerun.
