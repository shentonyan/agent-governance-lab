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

---

# Pilots 2 and 3 (2026-10-14): harder probes, then a probability readout

Status: exploratory. These runs informed `PREREG.md` v1 and are not part of the analysis.

## Pilot 2: harder probes, sampled choices

`data/probes/exp01_pilot2.jsonl` rewrote the bad options as warm, tone-matched replies and raised
the situational pressure; `data/probes/exp01_f1_pool.jsonl` extended F1 to 40 scenarios. Models:
`qwen2.5:7b`, `llama3.1:8b`, `gemma4:26b`, condition C0, both option orders.

Result: the sampled primary-class rate was still about 6% on F1 and 0–8% on F2/F3 for all three
models. Almost no choice was content-driven: where a model picked the primary option, it mostly
did so in only one of the two option orders (position effect), and picks in both orders were zero
on F1. Sampled forced choice therefore has no usable resolution here.

## Pilot 3: probability readout

Reading the answer-letter log-probabilities (see `PREREG.md`, "Readout") removes sampling noise.
C0, English, F1 = 40 scenarios, F2 and F3 = 6 each:

| model | family | mean P(primary) | log-odds mean (SD) | note |
|---|---|---|---|---|
| `qwen2.5:7b` | F1 | 0.088 | −11.5 (5.1) | many values clipped at ln(1e-6) = −13.8; saturated |
| `qwen2.5:7b` | F2 / F3 | 0.083 / 0.000 | −11.7 / −13.3 | saturated |
| `llama3.1:8b` | F1 | 0.070 | −6.4 (2.6) | unclipped, real spread; 5 of 40 scenarios with mean P in [0.1, 0.9] |
| `llama3.1:8b` | F2 / F3 | 0.008 / 0.015 | −7.5 / −7.0 | below the 10% line |
| `gemma4:26b` | all | – | – | 116 of 116 prompts unreadable: the model opens with a code fence, so the answer letter is not at the read position |

`llama3.1:8b` was chosen as primary model on this basis. By the original 10–90% rule no family
passes (F1 is at 7%); `PREREG.md` declares the resulting deviation explicitly.
