"""Dense + BM25 hybrid index with a local Ollama embedder.

The score is ``(1 - beta) * cosine + beta * bm25 / max_bm25`` (beta = 0.3, the upstream default
for its hybrid retrieval), multiplied by an optional per-document weight. Embedding calls go to
a loopback Ollama only; proxies from the environment are ignored.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
import numpy.typing as npt
import requests

from agent_governance_lab.backend.seeded_ollama import assert_loopback
from agent_governance_lab.memory.bm25 import BM25

Embedder = Callable[[Sequence[str]], npt.NDArray[np.float64]]


def ollama_embedder(
    model: str = "nomic-embed-text",
    base_url: str = "http://127.0.0.1:11434",
    timeout: float = 120.0,
) -> Embedder:
    assert_loopback(base_url)
    session = requests.Session()  # one keep-alive connection; avoids socket exhaustion on Windows
    session.trust_env = False

    def embed(texts: Sequence[str]) -> npt.NDArray[np.float64]:
        resp = session.post(
            f"{base_url.rstrip('/')}/api/embed",
            json={"model": model, "input": list(texts)},
            timeout=timeout,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        arr = np.asarray(data["embeddings"], dtype=np.float64)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        out: npt.NDArray[np.float64] = arr / np.where(norms == 0, 1.0, norms)
        return out

    return embed


class HybridIndex:
    """Same interface as :class:`BM25` (add, remove, search)."""

    def __init__(self, embed: Embedder, beta: float = 0.3) -> None:
        self.embed = embed
        self.beta = beta
        self.lex = BM25()
        self.vecs: list[npt.NDArray[np.float64]] = []
        self._stack: npt.NDArray[np.float64] | None = None

    def add(self, text: str) -> int:
        idx = self.lex.add(text)
        self.vecs.append(self.embed([text])[0])
        self._stack = None
        return idx

    def remove(self, idx: int) -> None:
        self.lex.remove(idx)

    def search(
        self, query: str, k: int = 5, weights: dict[int, float] | None = None
    ) -> list[tuple[int, float]]:
        if not self.vecs:
            return []
        if self._stack is None:
            self._stack = np.vstack(self.vecs)
        q = self.embed([query])[0]
        cos = self._stack @ q
        lex = dict(self.lex.search(query, len(self.vecs)))
        top = max(lex.values()) if lex else 0.0
        scores: list[tuple[int, float]] = []
        for i in range(len(self.vecs)):
            if not self.lex.alive[i]:
                continue
            s = (1 - self.beta) * float(cos[i]) + self.beta * (
                lex.get(i, 0.0) / top if top else 0.0
            )
            scores.append((i, s * (weights.get(i, 1.0) if weights else 1.0)))
        return sorted(scores, key=lambda kv: (-kv[1], kv[0]))[:k]
