# Experiment 1: Axiom-4 wording comparison (PRE-REGISTRATION DRAFT)

Status: **draft, not frozen**. Freeze = git tag `prereg-exp01` before any non-pilot run.

## Question
Does changing only the axiom-4 heading term and/or body term (care vs compassion; en and zh)
change agent behavior on fixed probes beyond a pre-set equivalence margin?

## Conditions (draft)
See `src/agent_governance_lab/constitutions/variants.py`: C1–C4 (en), E1 (heading removed), C5–C8 (zh).
The unmodified upstream text is the reference arm.

## Design
- One process per condition; seeded backend; all calls in the ledger.
- Same probe set, same seeds across conditions (paired).
- Probe items from the same scenario form one cluster.

## Analysis
- Primary: paired cluster bootstrap on per-item score difference vs reference.
- Equivalence margin: ±5 percentage points (CI-inclusion).
- Multiplicity: Holm across the condition family.
- Binary outcomes also reported with Wilson intervals; paired binary comparisons with exact McNemar.

## Not yet decided (must be fixed before freezing)
Probe set contents and size, outcome scoring rubric, number of seeds, model tag.
