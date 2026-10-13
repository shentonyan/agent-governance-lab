# Experiment 1: pilot run (2026-10-14)

Status: exploratory. Not part of the pre-registered analysis.

## What was run

- 18 scenarios (F1, F2, F3: six each; English and Chinese texts, matched), forced-choice JSON,
  both option orders, 3 seeds.
- `qwen2.5:7b`: conditions C0 (no axioms), C1, C2, C3, C4 in English (108 calls each), and C0 in
  Chinese (108 calls).
- `llama3.1:8b`: C0 and C1 in English (108 calls each).
- Ollama 0.34.2. All 1,080 calls returned a valid choice. Ledgers verify.

## Result

The share of the pre-registered primary class (comforting-but-untrue reply, dissuade/refuse,
harm-the-third-party) was 0.000 in every cell for `qwen2.5:7b`, and 0.000 in every cell but one for
`llama3.1:8b` (C1, F2: 1 of 36 calls, a refusal).

## Interpretation

This is a floor effect, not evidence that the wording is irrelevant. Both models pick the honest or
supportive option every time, with or without the axioms, so these probes cannot separate
conditions. An equivalence test on them would pass trivially and mean nothing.

Likely causes, to be checked rather than assumed: the unsafe options are written too plainly
(they state the falsehood or the harm outright), and instruction-tuned models handle that contrast
easily.

## Consequence for the design

1. Probes must be made harder before the pre-registration is frozen: the primary-class option
   should be a plausible, kind-sounding reply, and the situation should create real pressure toward it.
2. A sensitivity gate is added to the pre-registration (see PREREG.md): equivalence claims are only
   made on probe families where the C0 primary-class rate is between 10% and 90% in the pilot.
3. The next pilot should include at least one larger model (`gemma4:26b` is installed) to see
   whether any family has headroom.

Raw result files are in `runs/` (not committed).
