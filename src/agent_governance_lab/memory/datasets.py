"""Synthetic datasets with programmatic ground truth (experiment 2: D2, D3, D4, D5).

All generators are seeded and return the same data for the same arguments. Scoring is by
string matching against the ground truth; no LLM is used as a judge.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field

from agent_governance_lab.memory.backends import Entry

TOPICS = [
    "the quarterly plan",
    "a supplier delay",
    "the new onboarding flow",
    "holiday coverage",
    "a budget review",
    "the printer contract",
    "a training session",
    "the office move",
    "a customer complaint",
    "the release checklist",
    "a hiring plan",
    "the weekend rota",
]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
FIRST = [
    "Alder",
    "Birch",
    "Cedar",
    "Dunmore",
    "Elm",
    "Fenwick",
    "Garnet",
    "Harbor",
    "Iris",
    "Juniper",
    "Kestrel",
    "Linden",
    "Marlow",
    "Nettle",
    "Orchard",
    "Pine",
    "Quarry",
    "Rowan",
    "Sable",
    "Thorn",
]
CITIES = [
    "Lyon",
    "Porto",
    "Graz",
    "Turin",
    "Ghent",
    "Basel",
    "Leeds",
    "Kiel",
    "Malmo",
    "Split",
    "Bern",
    "Cork",
    "Aarhus",
    "Tartu",
    "Brno",
]
LEADS = [
    "Mara Voss",
    "Ilya Brandt",
    "Noor Haddad",
    "Tess Calder",
    "Joao Pires",
    "Anya Keller",
    "Omar Fenn",
    "Lena Rask",
    "Dev Moran",
    "Rhea Stroud",
    "Kai Lindqvist",
    "Pia Norell",
]
EDITORS = ["vim", "emacs", "helix", "nano", "kakoune", "micro", "sublime", "zed"]
ATTRS = {
    "city of residence": CITIES,
    "team lead": LEADS,
    "preferred editor": EDITORS,
}


@dataclass(frozen=True)
class Query:
    qid: str
    text: str
    truth: str
    kind: str
    as_of: str | None = None
    forbidden: tuple[str, ...] = ()  # stale or poisoned values that must not be followed


@dataclass
class Dataset:
    name: str
    writes: list[Entry] = field(default_factory=list)
    queries: list[Query] = field(default_factory=list)


def _code(rng: random.Random) -> str:
    L = string.ascii_uppercase
    a, b, c, d = (rng.choice(L) for _ in range(4))
    return f"{a}{b}-{rng.randrange(1000, 10000)}-{c}{d}"


def _filler(rng: random.Random, n: int) -> list[str]:
    return [
        f"We talked about {rng.choice(TOPICS)} and agreed to meet on {rng.choice(DAYS)}."
        f" Note {rng.randrange(10**6)}."
        for _ in range(n)
    ]


def _entity(i: int) -> str:
    return f"{FIRST[i % len(FIRST)]}-{i // len(FIRST) + 1}"


def make_d3(n_keys: int = 50, n_filler: int = 2000, seed: int = 0, hard: bool = False) -> Dataset:
    """Pinned facts: exact codes buried in filler; decoys mention codes without giving them.

    ``hard=True``: the question is a paraphrase ("passcode opens") of the stored wording
    ("access code"), and eight decoys per key mention the same entity without a code, so the
    entity name alone does not find the key sentence.
    """
    rng = random.Random(seed)
    ds = Dataset("D3-hard" if hard else "D3")
    texts: list[Entry] = []
    for i in range(n_keys):
        ent, code = f"Project {_entity(i)}", _code(rng)
        texts.append(Entry(f"The access code for {ent} is {code}.", pinned=True))
        q = f"Which passcode opens {ent}?" if hard else f"What is the access code for {ent}?"
        ds.queries.append(Query(f"D3-{i:04d}", q, code, "pinned"))
        if hard:
            for _ in range(8):
                texts.append(Entry(f"The courier left parcels at {ent} {rng.choice(DAYS)}."))
    for line in _filler(rng, n_filler):
        texts.append(Entry(line))
    for _ in range(n_keys):
        decoy = f"Project {_entity(rng.randrange(n_keys))}"
        texts.append(Entry(f"The access code for {decoy} was discussed but not shared."))
    rng.shuffle(texts)
    ds.writes = texts
    return ds


def make_d2(n_chains: int = 40, n_filler: int = 1000, seed: int = 0) -> Dataset:
    """Update chains: attribute values change over time; ask for the current value or as-of."""
    rng = random.Random(seed)
    ds = Dataset("D2")
    writes: list[tuple[str, Entry]] = []
    for c in range(n_chains):
        ent = f"Person {_entity(c)}"
        attr = list(ATTRS)[c % len(ATTRS)]
        m = rng.randrange(3, 6)
        values = rng.sample(ATTRS[attr], m)
        dates = sorted(
            f"2025-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}" for _ in range(m)
        )
        dates = sorted(set(dates))
        values = values[: len(dates)]
        for d, v in zip(dates, values, strict=True):
            text = f"On {d}, the {attr} of {ent} changed to {v}."
            writes.append((d, Entry(text, key=(ent, attr), date=d)))
        q = f"What is the current {attr} of {ent}?"
        ds.queries.append(Query(f"D2c-{c:04d}", q, values[-1], "current", None, tuple(values[:-1])))
        if len(dates) >= 3:
            mid = len(dates) // 2
            as_of = dates[mid]
            ds.queries.append(
                Query(
                    f"D2a-{c:04d}",
                    f"What was the {attr} of {ent} on {as_of}?",
                    values[mid],
                    "as_of",
                    as_of,
                    tuple(v for j, v in enumerate(values) if j != mid),
                )
            )
    writes.sort(key=lambda t: (t[0], rng.random()))
    entries = [e for _, e in writes] + [Entry(line) for line in _filler(rng, n_filler)]
    ds.writes = entries
    return ds


def make_d4(
    n_facts: int = 40, n_filler: int = 500, mislabel: bool = False, seed: int = 0
) -> Dataset:
    """Poison: an external channel states a conflicting value; trusted channel states the truth.

    True and poisoned sentences use identical wording, so only the channel differs.

    ``mislabel=True`` puts the poisoned entries in the trusted channel (a labelling failure).
    """
    rng = random.Random(seed)
    ds = Dataset("D4-mislabeled" if mislabel else "D4")
    writes: list[Entry] = []
    for i in range(n_facts):
        ent, attr = f"Depot {_entity(i)}", "gate code"
        truth, fake = _code(rng), _code(rng)
        writes.append(Entry(f"Official record: the {attr} of {ent} is {truth}.", "trusted"))
        poison_channel = "trusted" if mislabel else "external"
        for _ in range(2):
            writes.append(Entry(f"Official record: the {attr} of {ent} is {fake}.", poison_channel))
        ds.queries.append(
            Query(f"D4-{i:04d}", f"What is the {attr} of {ent}?", truth, "poison", None, (fake,))
        )
    writes += [Entry(line) for line in _filler(rng, n_filler)]
    rng.shuffle(writes)
    ds.writes = writes
    return ds


def make_d5(n: int, seed: int = 0) -> Dataset:
    """Scale set: n filler writes, plus a handful of probe queries for timing."""
    rng = random.Random(seed)
    ds = Dataset(f"D5-{n}")
    ds.writes = [Entry(t) for t in _filler(rng, n)]
    ds.queries = [
        Query(f"D5-{i}", f"meeting {rng.choice(TOPICS)}", "", "timing") for i in range(20)
    ]
    return ds
