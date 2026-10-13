# ADR 0003: Pre-registration before data

Status: accepted

## Decision
Each experiment has a `PREREG.md` (hypotheses, conditions, metrics, equivalence margin, correction,
stopping rule). It is frozen by a git tag before the first non-pilot run. Later changes are
amendments recorded in the same file, not edits to the frozen text.

## Consequences
Exploratory findings must be labelled as such.
