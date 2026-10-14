"""Spike: can the upstream distill pipeline be driven with our seeded backend?

Runs ``distill`` on a small synthetic episode log (D3-style) with ``view_registry=None``
(no noise gating) and reports how many of the exact codes survive in the distilled patterns.
Not part of the test suite; needs a running Ollama with the model and ``nomic-embed-text``.
Usage: python scripts/spike_b1.py [n_keys] [n_filler] [model]
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "third_party" / "contemplative-agent" / "src"))
sys.path.insert(0, str(ROOT / "src"))

from contemplative_agent.core import llm  # noqa: E402
from contemplative_agent.core.distill import distill  # noqa: E402
from contemplative_agent.core.knowledge_store import KnowledgeStore  # noqa: E402

from agent_governance_lab.backend.seeded_ollama import SeededOllamaBackend  # noqa: E402
from agent_governance_lab.ledger import Ledger  # noqa: E402
from agent_governance_lab.memory.datasets import make_d3  # noqa: E402


def main() -> None:
    n_keys = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    n_filler = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    model = sys.argv[3] if len(sys.argv) > 3 else "llama3.1:8b"
    ds = make_d3(n_keys, n_filler, seed=0)
    tmp = Path(tempfile.mkdtemp(prefix="spike-b1-"))
    log = tmp / "episodes.jsonl"
    with log.open("w", encoding="utf-8") as fh:
        for i, e in enumerate(ds.writes):
            rec = {
                "ts": f"2025-01-01T{(i // 60) % 24:02d}:{i % 60:02d}:00",
                "type": "interaction",
                "data": {
                    "direction": "received",
                    "agent_name": "peer",
                    "content_summary": e.text,
                },
            }
            fh.write(json.dumps(rec) + "\n")
    backend = SeededOllamaBackend(model, Ledger(tmp / "ledger.jsonl"), temperature=0.0)
    llm.configure(backend=backend)
    store = KnowledgeStore(tmp / "knowledge.json")
    distill(log_files=[log], knowledge_store=store, view_registry=None, dry_run=False)
    store.load()
    pats = store.get_live_patterns()
    text = "\n".join(str(p.get("pattern", p)) for p in pats)
    kept = sum(1 for q in ds.queries if q.truth in text)
    print(f"episodes={len(ds.writes)} llm_calls={backend.calls} patterns={len(pats)}")
    print(f"exact codes surviving in patterns: {kept}/{len(ds.queries)}")
    print("sample pattern:", text[:300].replace("\n", " | "))
    print("workdir:", tmp)


if __name__ == "__main__":
    main()
