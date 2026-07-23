# Evidence Citation Format

Use:

```text
repository/path#Lstart-Lend@sha256:<64 lowercase hex>
```

Requirements:

- repository-relative path only;
- no absolute path or `..` traversal;
- source must be a regular file, not a symlink;
- line range reflects the cited file at issue time;
- SHA-256 binds the citation to exact bytes;
- missing or unreadable evidence blocks Finding issuance.

A later byte change does not rewrite the citation. Add a correction addendum with the new citation.
