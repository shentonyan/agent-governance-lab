"""Small BM25 index (no dependencies) used by the memory baselines."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

_TOKEN = re.compile(r"[A-Za-z0-9一-鿿][A-Za-z0-9_\-一-鿿]*")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.docs: list[Counter[str]] = []
        self.lengths: list[int] = []
        self.postings: dict[str, list[int]] = defaultdict(list)
        self.alive: list[bool] = []
        self._total_len = 0

    def add(self, text: str) -> int:
        toks = tokenize(text)
        idx = len(self.docs)
        tf = Counter(toks)
        self.docs.append(tf)
        self.lengths.append(len(toks))
        self.alive.append(True)
        self._total_len += len(toks)
        for t in tf:
            self.postings[t].append(idx)
        return idx

    def remove(self, idx: int) -> None:
        self.alive[idx] = False

    def search(
        self, query: str, k: int = 5, weights: dict[int, float] | None = None
    ) -> list[tuple[int, float]]:
        n_alive = sum(self.alive)
        if n_alive == 0:
            return []
        avg = self._total_len / len(self.docs) or 1.0
        scores: dict[int, float] = defaultdict(float)
        for t in set(tokenize(query)):
            plist = [i for i in self.postings.get(t, ()) if self.alive[i]]
            if not plist:
                continue
            idf = math.log(1 + (n_alive - len(plist) + 0.5) / (len(plist) + 0.5))
            for i in plist:
                tf = self.docs[i][t]
                denom = tf + self.k1 * (1 - self.b + self.b * self.lengths[i] / avg)
                scores[i] += idf * tf * (self.k1 + 1) / denom
        if weights:
            for i in scores:
                scores[i] *= weights.get(i, 1.0)
        return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
