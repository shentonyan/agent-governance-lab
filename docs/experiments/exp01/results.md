# Experiment 1: results (pre-registration v1)

Run 2026-10-14 with `llama3.1:8b`, English, F1 (40 scenarios), one deterministic readout per
condition, as specified in [`PREREG.md`](PREREG.md) (tag `prereg-exp01-v1`). Ledgers verify (12 of 12).

## Confirmatory contrasts against C1 (F1, log-odds of comforting-false vs honest, orders averaged)

Bonferroni CI for 4 contrasts (98.75%), paired scenario-clustered bootstrap.

| contrast | n | mean difference | CI | reading |
|---|---|---|---|---|
| C2 - C1 | 40 | 0.000 | [-0.057, 0.054] | no difference detected |
| C3 - C1 | 40 | -0.013 | [-0.082, 0.057] | no difference detected |
| C4 - C1 | 40 | -0.038 | [-0.101, 0.027] | no difference detected |
| E1 - C1 | 40 | -0.040 | [-0.154, 0.064] | no difference detected |

Per the pre-registration this is worded "no difference detected on F1 with this model", not
"equivalent", even though every CI lies inside the +-0.5 margin: only 1 of 40 scenarios has
P(comforting-false) of at least 0.1 under C1, so the probe set has little headroom.

## Manipulation check (descriptive)

C0 (no axioms) minus C1: -0.089, CI [-0.424, 0.265] (unadjusted comparison; not a confirmatory test).
Mean P(comforting-false) is 0.055 under C0 and 0.015 under C1; scenarios with P at least 0.1: 5 under
C0, 1 under C1. The axioms may lower the rate on the few scenarios with headroom, but this was not
tested and the log-odds mean barely moves (-6.40 vs -6.31).

## Reproducibility

The formal C0 readout reproduces the pilot C0 readout exactly (maximum absolute difference in
probability 0.0 over 80 prompts).

## Exploratory (F2, F3; 6 scenarios each; no tests)

Mean P(primary class) for C0, C1, C2, C3, C4, E1: F2 = 0.008, 0.040, 0.040, 0.035, 0.044, 0.053;
F3 = 0.015, 0.025, 0.029, 0.028, 0.025, 0.014. All near the floor. The six F1 scenarios in this
file were also run and are not part of the confirmatory analysis.

## Limits

One model, English only, one readout per condition, a length confound in the options, weak headroom,
and a sensitivity gate relaxed after pilot data (see `PREREG.md`, "Deviations", and
`docs/threats-to-validity.md`). A one-word wording change has no detectable effect on this probe
set; that does not show the wording is irrelevant for other models, probes or behaviours.
