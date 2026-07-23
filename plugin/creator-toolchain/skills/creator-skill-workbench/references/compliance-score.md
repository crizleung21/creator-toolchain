# Reproducible Compliance Score

## Dimensions

| Dimension | Weight |
|---|---:|
| Trigger precision | 15 |
| Boundary clarity | 15 |
| Workflow completeness | 20 |
| Progressive disclosure | 15 |
| State safety | 10 |
| Reference integrity | 10 |
| Acceptance tests | 10 |
| Naming and collision | 5 |
| **Total** | **100** |

## Status Bands

| Score | Status | Packaging guidance |
|---:|---|---|
| 90–100 | compliant | ready after all other release gates |
| 70–89 | partial | usable with documented remediation |
| 40–69 | weak | do not package |
| 0–39 | non-compliant | rewrite required |

## Evidence Rule

Every lost point must identify the dimension, point value, check ID, and observable evidence. No deduction may rely only on stylistic preference.
