"""B1: the upstream distillation pipeline used as a memory backend.

Entries become episode records, the upstream ``distill`` turns batches of episodes into
patterns through an LLM, and retrieval runs over the resulting live patterns with the same
hybrid index as the other dense backends. The harness imports upstream code only here, and only
``distill`` and ``KnowledgeStore`` (never the CLI).

Mapping of channels to upstream provenance (ADR-0021): ``external`` entries become
``interaction`` episodes with direction ``received`` (external_reply), ``trusted`` entries become
``insight`` episodes (self_reflection). The upstream summary of an episode is cut at 80
characters; the dataset sentences are shorter than that by construction.

Limits that apply to every B1 number: it needs a model that follows the upstream JSON
instruction (``llama3.1:8b`` returned prose and produced zero patterns in a spike), noise gating
is off (``view_registry=None``), and the pipeline has no as-of retrieval.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from agent_governance_lab.memory.backends import Entry
from agent_governance_lab.memory.hybrid import Embedder, HybridIndex

_ROOT = Path(__file__).resolve().parents[3]


def _import_upstream() -> tuple[Any, Any, Any]:
    try:
        from contemplative_agent.core import llm
    except ImportError:
        sys.path.insert(0, str(_ROOT / "third_party" / "contemplative-agent" / "src"))
        from contemplative_agent.core import llm
    from contemplative_agent.core.distill import distill
    from contemplative_agent.core.knowledge_store import KnowledgeStore

    return llm, distill, KnowledgeStore


class B1:
    name = "B1"

    def __init__(self, generator: Any, embed: Embedder, workdir: Path | None = None) -> None:
        self.generator = generator
        self.embed = embed
        self.workdir = workdir or Path(tempfile.mkdtemp(prefix="b1-"))
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = []
        self.index: HybridIndex | None = None
        self.patterns: list[str] = []

    def write(self, e: Entry) -> None:
        i = len(self.records)
        ts = f"2025-01-{1 + (i // 1440) % 28:02d}T{(i // 60) % 24:02d}:{i % 60:02d}:00"
        if e.channel == "external":
            rec = {
                "ts": ts,
                "type": "interaction",
                "data": {"direction": "received", "agent_name": "peer", "content_summary": e.text},
            }
        else:
            rec = {"ts": ts, "type": "insight", "data": {"observation": e.text}}
        self.records.append(rec)

    def finalize(self) -> None:
        llm, distill, knowledge_store = _import_upstream()
        log = self.workdir / "episodes.jsonl"
        with log.open("w", encoding="utf-8", newline="\n") as fh:
            for r in self.records:
                fh.write(json.dumps(r) + "\n")
        llm.configure(backend=self.generator)
        store = knowledge_store(self.workdir / "knowledge.json")
        distill(log_files=[log], knowledge_store=store, view_registry=None, dry_run=False)
        store.load()
        self.patterns = [str(p.get("pattern", "")) for p in store.get_live_patterns()]
        self.index = HybridIndex(self.embed)
        for p in self.patterns:
            if p:
                self.index.add(p)

    def retrieve(self, query: str, k: int = 5, as_of: str | None = None) -> list[str]:
        if self.index is None:
            raise RuntimeError("finalize() must run before retrieve()")
        texts = [p for p in self.patterns if p]
        return [texts[i] for i, _ in self.index.search(query, k)]
