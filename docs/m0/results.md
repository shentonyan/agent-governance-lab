# M0 smoke results

- model: `qwen2.5:7b`  seed: 0  num_predict: 64
- ollama: 0.34.2  python: 3.12.10  os: Windows
- date: 2026-10-14
- mean seconds per run of 3 calls: 0.9

| check | result |
|---|---|
| ledger verifies for every run | PASS |
| same seed, 2 runs: identical responses (3 prompts) | PASS |
| different seed: responses differ | PASS |
| en variants produce >= 3 distinct texts | PASS |

Scope: one model, one machine, short generations. This shows seeding is repeatable here;
it does not show repeatability across hardware or Ollama versions.

## Variant generation on the pinned upstream file

English variants C1-C4 and E1 were generated from the axioms file at the pinned rules revision. C4 (heading Care, body compassion) is byte-identical to the original; the others differ only inside the axiom-4 section.
