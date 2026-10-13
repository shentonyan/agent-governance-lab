# agent-governance-lab

A small, reproducible harness for experiments on how an agent's governance artifacts behave
when run on a local model: constitution wording, tiered memory, and multi-stage skill review.

It sits **above** [contemplative-agent](https://github.com/shentonyan/contemplative-agent)
(a fork of shimo4228/contemplative-agent) and does not modify it. The harness injects a seeded
LLM backend, records every model call in a tamper-evident ledger, and runs one process per
experimental condition.

## Status

Milestone M1 (core utilities). No experiment results exist yet. Experiment 1 has a draft
pre-registration in [`docs/experiments/exp01/PREREG.md`](docs/experiments/exp01/PREREG.md);
it is not frozen.

| Component | State |
|---|---|
| Hash-chained run ledger | implemented, tested |
| Seeded, loopback-only Ollama backend | implemented, tested with a fake transport |
| Axiom-4 wording variant generator (en/zh) | implemented, tested on synthetic text |
| Statistics (Wilson, exact McNemar, Holm, cluster bootstrap, equivalence, phi) | implemented, tested |
| M0 self-check against a real Ollama | implemented; not yet run on real hardware |
| Experiments 1–3 | designed, not run |

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
agl self-check --model <your-ollama-model-tag>
```

CLI: `agl verify-ledger <file>`, `agl make-variants --axioms <md> --lang en|zh --out <dir>`,
`agl self-check --model <tag>`.

## Design rules

- Upstream code is not vendored or edited; see `docs/adr/`.
- Every model call is appended to a hash-chained ledger; `agl verify-ledger` re-checks it.
- Only loopback model endpoints are accepted, and system proxies are ignored.
- Hypotheses, metrics and stopping rules are written down before data is collected.
- Seeding gives repeatability on one machine and build, not a cross-hardware guarantee;
  M0 measures it.
- Raw data and run outputs are not committed (`data/raw/`, `runs/`).

## Layout

```
src/agent_governance_lab/   library and CLI
tests/                      unit tests (no network, no model)
docs/adr/                   architecture decision records
docs/experiments/           pre-registrations and protocols
docs/threats-to-validity.md
scripts/                    setup and upstream fetch helpers
```

## License

MIT for this repository's own code and text. Upstream material keeps its own licenses; see
[`THIRD_PARTY.md`](THIRD_PARTY.md).
