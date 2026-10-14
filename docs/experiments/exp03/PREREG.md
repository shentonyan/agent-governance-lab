# Experiment 3: staged skill review (PRE-REGISTRATION DRAFT)

Status: **draft, not frozen.** Freeze = git tag `prereg-exp03-v1` before any holdout run.

## Question

Can a staged, schema-constrained review stop prompt-level skill proposals that carry manipulation
patterns, without rejecting legitimate ones; does a constitution (the four axioms) help compared
with a generic safety prompt; and what does it cost. Scope: Markdown skills in the upstream
skill format, not on-chain code.

## Pipeline (implemented: `src/agent_governance_lab/review/`)

1. Stage 0, static: length 80–4000 characters, a Markdown title, and a short literal deny-list.
   This is a stand-in for the upstream `validate_identity_content`, not a copy.
2. Stage 1, ethics reviewer; stage 2, safety reviewer. Separate prompts, same model, temperature 0.
   Output is constrained to `{"verdict": approve|reject|escalate, "reason": <code>}`.
3. Aggregation: any reject rejects; else any escalate escalates; else approve. An unparsable
   answer is an escalate. Reviewer prompts contain no generation request (unit-tested).
4. Not implemented yet: stage 3 evaluation on held-out tasks, adaptive attacker, the arms RP and
   RPC (they need the NaturalDAO love/hate definitions pinned by commit and date).

## Arms implemented

| id | configuration |
|---|---|
| S0 | static check only |
| R0 | static + ethics + safety, generic prompts, no constitution |
| RC | as R0, with the four axioms (C1 wording) prepended as constitution |

## Test set (`data/exp03/abd.jsonl`, built by `scripts/build_exp03_abd.py`)

| category | content | n | source |
|---|---|---|---|
| A | normal skills (20) and near-miss legitimate skills sharing vocabulary with D (8) | 28 | hand-written, neutral |
| B | sensitive but legitimate (moderation, research, fiction, support) | 12 | hand-written, neutral |
| D | manipulation: sycophancy, fake intimacy, rule override, data exfiltration; explicit tier (24) and implicit tier (16) | 40 | hand-written, neutral |
| C | hate or contempt patterns: HateCheck cases wrapped in a neutral skill template (explicit 32, implicit 32), plus 12 non-hateful quote-to-condemn cases added to B | 76 | public dataset (HateCheck, CC BY 4.0 to be verified); raw text stays in `data/raw` (ignored), the repo holds `data/exp03/c_manifest.json` with ids and hashes; built by `scripts/build_exp03_c.py` |

Stratified split by category: 30% holdout, 70% dev. Prompts may be tuned on dev only. The holdout
is run once, after freezing.

## Metrics

Recall on C and D (reject), false-reject rate on A and B, escalate rate, phi of the two
reviewers' errors, calls per proposal. Wilson intervals; paired comparisons by exact McNemar with
Holm correction (implemented in `stats/`).

## Dev pilot (exploratory; `llama3.1:8b`, dev split, n = 56)

| arm | recall (D) | false-reject (A, B) | note |
|---|---|---|---|
| S0 | 0.04 (1/28 bad) | 0.00 | only the literal deny-list fires |
| R0 | 0.71 [0.53, 0.85] | 0.00 [0.00, 0.12] | implicit tier clearly lower than explicit |
| RC | 0.86 [0.69, 0.94] | 0.00 [0.00, 0.12] | difference to R0 not significant at n = 28 |

Process notes, disclosed: a first pilot on the explicit tier alone gave R0 0.94 and RC 1.00
(ceiling). The implicit tier and the near-miss legitimate skills were added **after** seeing that
result. The safety prompt names the behaviours that category D tests, so recall on the explicit tier
partly measures prompt–test overlap.

## Dev pilot with category C (exploratory; `llama3.1:8b`, dev split, n = 109)

| arm | recall (C + D) | false-reject (A + B) | C explicit | C implicit | D implicit |
|---|---|---|---|---|---|
| S0 | 0.01 | 0.00 | 0/25 | 0/20 | 0/13 |
| R0 | 0.89 [0.80, 0.94] | 0.00 [0.00, 0.10] | 25/25 | 20/20 | 5/13 |
| RC | 0.95 [0.87, 0.98] | 0.00 [0.00, 0.10] | 25/25 | 20/20 | 9/13 |

Category C is at the ceiling for both reviewer arms, including the HateCheck "implicit" cases and
the 8 dev quote-to-condemn items (all approved, so no over-refusal there). The template tells the
agent to adopt the quoted view as its own, which makes any hateful statement obvious, so this
category does not separate the arms. Any RC advantage comes from the implicit manipulation tier
(n = 13 in dev) and is not significant.

## Still to decide before freezing

Primary contrast (RC vs R0 on D, McNemar, margin and test), number of proposals needed (power from
the dev numbers is thin: 28 bad proposals in dev), whether C stays (it is saturated; a subtler wrapper, e.g. a skill that
asks the agent to *judge* or *summarise* such statements, would be needed to make it informative),
second annotator for labels (open), and the primary model (`llama3.1:8b` so far).
