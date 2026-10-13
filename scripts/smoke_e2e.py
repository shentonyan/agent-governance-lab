"""End-to-end smoke run against a local Ollama; writes docs/m0/results.md.

Usage: python scripts/smoke_e2e.py --model <tag> [--seed 0] [--repeats 2]

Checks: ledger written and verified for every run, repeated runs with the same seed give
identical response hashes, axiom-variant generation works. Output contains no paths or hostnames.
"""

from __future__ import annotations

import argparse
import json
import platform
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

from agent_governance_lab.backend import SeededOllamaBackend
from agent_governance_lab.constitutions import VARIANTS, make_variant
from agent_governance_lab.ledger import Ledger, verify_ledger

PROMPTS = [
    "Name three prime numbers greater than 100, comma separated.",
    "In one sentence, what is a hash chain?",
    "Write two short sentences about patience.",
]
AXIOM_FIXTURE = "## 4. Boundless Care\nAct with compassion; offer compassionate attention.\n"


def ollama_version(base_url: str) -> str:
    with requests.Session() as s:
        s.trust_env = False
        return str(s.get(f"{base_url}/api/version", timeout=10).json().get("version", "?"))


def one_run(model: str, seed: int, tmp: Path, tag: str, num_predict: int) -> dict[str, Any]:
    path = tmp / f"{tag}.jsonl"
    backend = SeededOllamaBackend(model, Ledger(path), base_seed=seed)
    t0 = time.perf_counter()
    outs = [backend.generate(p, num_predict=num_predict) for p in PROMPTS]
    dt = time.perf_counter() - t0
    rep = verify_ledger(path)
    hashes = [
        json.loads(line)["payload"]["response_sha256"]
        for line in path.read_text("utf-8").splitlines()
    ]
    return {"ok": rep.ok, "entries": rep.entries, "hashes": hashes, "seconds": dt, "outs": outs}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--num-predict", type=int, default=64)
    ap.add_argument("--out", default="docs/m0/results.md")
    a = ap.parse_args()
    base = "http://127.0.0.1:11434"

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        runs = [one_run(a.model, a.seed, tmp, f"r{i}", a.num_predict) for i in range(a.repeats)]
        other = one_run(a.model, a.seed + 1, tmp, "other", a.num_predict)
    same = all(r["hashes"] == runs[0]["hashes"] for r in runs)
    differs = other["hashes"] != runs[0]["hashes"]
    variants = {
        vid: make_variant(AXIOM_FIXTURE, vid) for vid, v in VARIANTS.items() if v.lang == "en"
    }
    variants_ok = len({v for v in variants.values()}) >= 3
    ledgers_ok = all(r["ok"] for r in [*runs, other])

    rows = [
        ("ledger verifies for every run", ledgers_ok),
        (f"same seed, {a.repeats} runs: identical responses ({len(PROMPTS)} prompts)", same),
        ("different seed: responses differ", differs),
        ("en variants produce >= 3 distinct texts", variants_ok),
    ]
    lines = [
        "# M0 smoke results",
        "",
        f"- model: `{a.model}`  seed: {a.seed}  num_predict: {a.num_predict}",
        f"- ollama: {ollama_version(base)}  python: {platform.python_version()}"
        f"  os: {platform.system()}",
        f"- date: {time.strftime('%Y-%m-%d')}",
        f"- mean seconds per run of {len(PROMPTS)} calls: "
        f"{sum(r['seconds'] for r in runs) / len(runs):.1f}",
        "",
        "| check | result |",
        "|---|---|",
        *[f"| {n} | {'PASS' if ok else 'FAIL'} |" for n, ok in rows],
        "",
        "Scope: one model, one machine, short generations. This shows seeding is repeatable here;",
        "it does not show repeatability across hardware or Ollama versions.",
    ]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0 if all(ok for _, ok in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
