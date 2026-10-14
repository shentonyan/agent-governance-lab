# Experiment 2: memory backends (PRE-REGISTRATION DRAFT)

Status: **draft, not frozen.** Freeze = git tag `prereg-exp02-v1` before any non-development run.

## Question

Which memory design meets the requirements in the NaturalDAO plan and the meeting notes, at what
cost, and what does the upstream distillation pipeline lack.

## Requirements and how each is tested

| id | requirement | test |
|---|---|---|
| R1 | large capacity, fast retrieval | D5 scale set: write time, query p50 and p95 |
| R2 | long-dialogue QA accuracy | D1 (LoCoMo), **not implemented** |
| R3 | new facts override old, multi-hop uses the new | D2 update chains |
| R4 | important items kept verbatim | D3 pinned facts |
| R5 | low-trust sources do not override high-trust | D4 poison set, with a mislabelled variant |
| R6, R7 | approval and audit; improves with use, portable storage | capability list, not scored |

## Backends

| id | status | description |
|---|---|---|
| B0 | implemented | flat BM25 over raw entries; ignores all metadata (floor baseline) |
| B1 | **not implemented** | upstream distillation pipeline (needs dialogue-episode support, checks M0 #5 and #6) |
| B2o | implemented, **oracle** | B0 plus a verbatim pinned layer, trust weights per channel, and supersession by (entity, attribute) key. The key is given by the caller, so B2o is an upper bound for what these mechanisms do when fact matching is solved. It is not a deployable system. |
| B3 | **not implemented** | OpenViking as an external process (AGPL-3.0, no code copied); local embedding and VLM needed (M0 #8) |

Retrieval is lexical (BM25) because no embedding model is installed. Scoring is by string match
against generated ground truth; no LLM judge. The same code path is used for all backends.

## Datasets (`src/agent_governance_lab/memory/datasets.py`, seeded)

D2 update chains (current value and as-of value), D3 pinned codes among filler with decoys,
D4 poison (conflicting external entries; variant with poison labelled trusted), D5 scale.

## Metrics

`hit`: ground-truth string is in the retrieved context (top k = 5). `top1_hit`: it is in the first
chunk. `top1_bad`: a stale or poisoned value is in the first chunk. Wilson intervals. Timing for D5.

## Development results (exploratory; seed 0, default sizes)

| dataset | B0 | B2o | reading |
|---|---|---|---|
| D2 current (n = 40) | top1_hit 0.00, top1_bad 40 | top1_hit 1.00 | B2o wins by construction: supersession uses the oracle key |
| D2 as-of (n = 40) | top1_hit 1.00 | top1_hit 1.00 | no difference |
| D3 pinned (n = 50, 2,100 writes) | hit 1.00 | hit 1.00 | **saturated**: BM25 on exact entity tokens is enough at this scale; no discrimination |
| D4 poison (n = 40) | top1_hit 0.38, top1_bad 25 | top1_hit 1.00 | trust weighting works when channels are labelled correctly |
| D4 mislabelled | top1_hit 0.38, top1_bad 25 | top1_hit 0.38, top1_bad 25 | the advantage disappears when labels are wrong |
| D5, 20,000 writes | query p50 4.8 ms, p95 6.9 ms | p50 6.8 ms, p95 8.5 ms | lexical index only; no LLM calls at write time |

## Not yet testable (and why)

The design's predictions P1 (the upstream pipeline loses verbatim strings), P2 (as-of versus
current) and P3 (OpenViking accuracy and cost) concern B1 and B3, which do not exist yet. D3 needs
a harder variant (more filler, paraphrased queries, an embedding retriever) before it can separate
anything.
