# ADR 0005: Data hygiene

Status: accepted

## Decision
- Raw datasets and run outputs are gitignored.
- Manifests are passed through `manifest.scrub` before sharing.
- Harmful-content test items come only from published datasets under their licenses; none are
  hand-written here.
- Tests use synthetic fixtures, not copies of published clauses.
