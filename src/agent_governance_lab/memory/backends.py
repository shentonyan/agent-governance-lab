"""Memory backends for experiment 2 (retrieval level; no LLM in the loop).

``B0`` is a flat BM25 store and ignores all metadata (the floor baseline).

``B2o`` adds three mechanisms that the upstream distillation pipeline does not provide:
a verbatim *pinned* layer, trust weights per source channel, and supersession of older
entries about the same (entity, attribute). **The (entity, attribute) key is given by the
caller (an oracle).** B2o therefore measures what the mechanisms can achieve when fact
matching is solved; a real system has to detect that two statements concern the same
attribute. Do not read B2o numbers as a property of a deployable system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agent_governance_lab.memory.bm25 import BM25

TRUST_WEIGHT = {"trusted": 1.0, "external": 0.3}


@dataclass(frozen=True)
class Entry:
    text: str
    channel: str = "trusted"  # "trusted" | "external"
    key: tuple[str, str] | None = None  # (entity, attribute), oracle metadata
    date: str | None = None  # ISO date, sortable as a string
    pinned: bool = False


class Backend(Protocol):
    def write(self, e: Entry) -> None: ...

    def retrieve(self, query: str, k: int = 5, as_of: str | None = None) -> list[str]: ...


class B0:
    name = "B0"

    def __init__(self) -> None:
        self.idx = BM25()
        self.entries: list[Entry] = []

    def write(self, e: Entry) -> None:
        self.idx.add(e.text)
        self.entries.append(e)

    def retrieve(self, query: str, k: int = 5, as_of: str | None = None) -> list[str]:
        return [self.entries[i].text for i, _ in self.idx.search(query, k)]


class B2o:
    name = "B2o"

    def __init__(self, pinned_slots: int = 2) -> None:
        self.main = BM25()
        self.pins = BM25()
        self.main_entries: list[Entry] = []
        self.pin_entries: list[Entry] = []
        self.latest: dict[tuple[str, str], int] = {}  # key -> main index of newest entry
        self.pinned_slots = pinned_slots

    def write(self, e: Entry) -> None:
        if e.pinned:
            self.pins.add(e.text)
            self.pin_entries.append(e)
            return
        idx = self.main.add(e.text)
        self.main_entries.append(e)
        if e.key is not None:
            prev = self.latest.get(e.key)
            if prev is None or (e.date or "") >= (self.main_entries[prev].date or ""):
                self.latest[e.key] = idx  # older entries stay stored, flagged by not being latest

    def _superseded(self, i: int) -> bool:
        e = self.main_entries[i]
        return e.key is not None and self.latest.get(e.key) != i

    def retrieve(self, query: str, k: int = 5, as_of: str | None = None) -> list[str]:
        out = [self.pin_entries[i].text for i, _ in self.pins.search(query, self.pinned_slots)]
        weights = {i: TRUST_WEIGHT.get(e.channel, 1.0) for i, e in enumerate(self.main_entries)}
        hits = self.main.search(query, k * 4, weights)
        for i, _ in hits:
            if len(out) >= k:
                break
            e = self.main_entries[i]
            if as_of is None and self._superseded(i):
                continue
            if as_of is not None and e.date is not None and e.date > as_of:
                continue
            out.append(e.text)
        return out[:k]


BACKENDS = {"B0": B0, "B2o": B2o}
