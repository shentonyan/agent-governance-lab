# Experiment 2: memory backends (PRE-REGISTRATION DRAFT)

Status: **draft, not frozen.** Freeze = git tag `prereg-exp02-v1` before any non-development run.
Everything below marked "development" is exploratory and may have shaped the design.

## Question

Which memory design meets the requirements in the NaturalDAO plan and the meeting notes, at what
cost, and what does the upstream distillation pipeline lack.

## Requirements and how each is tested

| id | requirement | test |
|---|---|---|
| R1 | large capacity, fast retrieval | D5 scale set: write time, query p50 and p95 |
| R2 | long-dialogue QA accuracy | D1 (LoCoMo), **not implemented** |
| R3 | new facts override old, multi-hop uses the new | D2 update chains (multi-hop not implemented) |
| R4 | important items kept verbatim | D3 pinned facts (plain and hard) |
| R5 | low-trust sources do not override high-trust | D4 poison set, plus a mislabelled variant |
| R6, R7 | approval and audit; improves with use, portable storage | capability list, not scored |

## Backends

| id | status | description |
|---|---|---|
| B0 | implemented | flat BM25 over raw entries; ignores all metadata (floor baseline) |
| B0h | implemented | B0 with hybrid retrieval: 0.7 cosine (`nomic-embed-text`) + 0.3 BM25 |
| B1 | implemented (spike scale) | upstream `distill` over episode records, then hybrid retrieval over the live patterns. Generator `qwen2.5:7b` (`llama3.1:8b` ignores the JSON instruction and yields no patterns). Noise gating off. |
| B2o, B2oh | implemented, **oracle** | B0 / B0h plus a verbatim pinned layer, per-channel trust weights, and supersession by (entity, attribute) key. The key, the pin flag and the channel label come from the dataset generator, so these are upper bounds for the mechanisms, not deployable systems. |
| B3 | **not implemented** | OpenViking as an external process (AGPL-3.0, no code copied); needs local embedding and VLM wiring (M0 #8) |

Scoring is by string match against generated ground truth; no LLM judge. Same code path for all
backends. Datasets are seeded (`src/agent_governance_lab/memory/datasets.py`).

## Datasets

D2 update chains (current and as-of). D3 pinned codes among filler; D3-hard adds a paraphrased
question and eight same-entity decoys per key, with decoy length matched to the key sentence.
D4 poison: conflicting entries from an external channel, identical wording to the true entry, so
only the channel differs; variant with the poison labelled trusted. D5 scale.

## Metrics

`hit`: the ground-truth string is in the top-5 context. `top1_hit`: it is in the first chunk.
`top1_bad`: a stale or poisoned value is in the first chunk. Wilson intervals. Timing for D5.

## Development results (exploratory; seed 0)

Default size (`runs/exp02-dev`, lexical and hybrid, no B1):

| dataset (n queries) | B0 | B0h | B2o / B2oh |
|---|---|---|---|
| D2 current (40), top1_hit | 0.00 | 0.28 | 1.00 |
| D2 as-of (40), top1_hit | 1.00 | 1.00 | 1.00 |
| D3 (50), hit | 1.00 | 1.00 | 1.00 |
| D3-hard (50), hit / top1_hit | 0.64 / 0.12 | 1.00 / 1.00 | 1.00 / 1.00 |
| D4 (40), top1_hit | 0.38 | 0.38 | 1.00 |
| D4 mislabelled (40), top1_hit | 0.38 | 0.38 | 0.38 |

Small size with B1 (`runs/exp02-b1`; D2 15 chains, D3 20 keys, D4 15 facts; B1 on `qwen2.5:7b`):

| dataset (n queries) | B1 hit | B0h hit | B2oh hit |
|---|---|---|---|
| D2 current (15) | 0.07 | 1.00 | 1.00 |
| D2 as-of (15) | 0.33 | 1.00 | 1.00 |
| D3 pinned (20) | 0.00 | 1.00 | 1.00 |
| D3-hard (20) | 0.05 | 1.00 | 1.00 |
| D4 poison (15) | 0.00 | 1.00 | 1.00 |

Reading, with limits:

- The distillation pipeline as used here does not keep exact strings: 0 of 20 codes (D3), 0 of 15
  (D4) and 1 of 20 (D3-hard) survive in its patterns. This is a spike at small scale with one
  generator model, not a general statement about the pipeline.
- Dense retrieval helps where wording differs (D3-hard: lexical 0.64, hybrid 1.00); it does not
  fix recency (D2 current, top1 0.28) or trust (D4, 0.38). Those need the metadata mechanisms.
- B2o/B2oh results on D2, D3 and D4 follow from oracle metadata and from the generator giving the
  pin flag. With wrong channel labels the trust advantage disappears (D4 mislabelled, 0.38).
- D3 (plain) is saturated for every retriever and is kept only as a sanity check.

D5 (lexical, 20,000 writes, earlier run): query p50 4.8 ms, p95 6.9 ms (B0); 6.8 and 8.5 ms (B2o).
Hybrid backends need one embedding call per write (about 15 s for 1,162 writes), B1 about one LLM
call per 10 episodes.

## Not yet testable (and why)

P3 (OpenViking accuracy and cost) needs B3. R2 needs LoCoMo (licence and download to verify). The
design's multi-hop question type is not generated. B1 at full dataset size has not been run.
