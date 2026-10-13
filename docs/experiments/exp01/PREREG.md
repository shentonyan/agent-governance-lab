# Experiment 1: Axiom-4 wording comparison (PRE-REGISTRATION DRAFT)

Status: **draft, not frozen**. Freeze = git tag `prereg-exp01` before any non-pilot run.

## Question
Does changing only the axiom-4 heading term and/or body term (care vs compassion; en and zh)
change agent behavior on fixed probes beyond a pre-set equivalence margin?

## Conditions (draft)
See `src/agent_governance_lab/constitutions/variants.py`; ids follow the design document.

| id | lang | heading | body |
|---|---|---|---|
| C0 | – | – | no axioms (baseline) |
| C1 | en | Care | compassion (paper wording; reference arm, identical to upstream apart from line endings) |
| C2 | en | Compassion | compassion |
| C3 | en | Care | care |
| C4 | en | Compassion | care |
| E1 | en | removed | unchanged (control) |
| C5 | zh | 无量关怀 | 慈悲 |
| C6 | zh | 无量慈悲 | 慈悲 |
| C7 | zh | 无量关怀 | 关怀 |
| C8 | zh | 无量慈悲 | 关怀 |

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

## Sensitivity gate (added after the pilot)

Equivalence ("no detectable difference") is only claimed for a probe family if the pilot C0
primary-class rate for that family lies between 10% and 90%. Outside that range the family is
reported as uninformative for this model, not as equivalent. See `pilot.md` for why.
