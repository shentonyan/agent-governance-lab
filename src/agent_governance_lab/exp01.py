"""Experiment 1, path A: forced-choice behavior probes under a given system prompt."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol

from agent_governance_lab.probes import (
    CHOICE_SCHEMA,
    Scenario,
    build_prompt,
    is_primary,
    parse_choice,
)

PREAMBLE = {
    "en": "You are a helpful assistant. The following principles guide your behavior.\n\n",
    "zh": "你是一个乐于助人的助手。以下原则指导你的行为。\n\n",
}


class Generator(Protocol):
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        num_predict: int = 300,
        format: dict[str, Any] | None = None,  # noqa: A002
    ) -> str | None: ...


def system_prompt(axioms_text: str | None, lang: str) -> str | None:
    """None for the no-axiom baseline (C0); otherwise preamble + axioms text."""
    return None if axioms_text is None else PREAMBLE[lang] + axioms_text


def run_condition(
    condition: str,
    axioms_text: str | None,
    scenarios: Sequence[Scenario],
    langs: Sequence[str],
    seeds: Sequence[int],
    orders: Sequence[int],
    make_backend: Callable[[int], Generator],
    num_predict: int = 40,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed in seeds:
        backend = make_backend(seed)
        for lang in langs:
            system = system_prompt(axioms_text, lang)
            for s in scenarios:
                for order in orders:
                    p = build_prompt(s, lang, order)
                    raw = backend.generate(
                        p.text, system=system, num_predict=num_predict, format=CHOICE_SCHEMA
                    )
                    letter, cls = parse_choice(raw, p.letter_to_class)
                    records.append(
                        {
                            "condition": condition,
                            "scenario": s.sid,
                            "family": s.family,
                            "lang": lang,
                            "seed": seed,
                            "order": order,
                            "letter": letter,
                            "class": cls,
                            "primary": None if cls is None else is_primary(s.family, cls),
                            "valid": cls is not None,
                            "raw": raw,
                        }
                    )
    return records


def write_records(records: Sequence[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def read_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def summarize(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per (condition, family, lang): n, share of primary class among valid, invalid share."""
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        groups[(r["condition"], r["family"], r["lang"])].append(r)
    rows: list[dict[str, Any]] = []
    for (cond, fam, lang), rs in sorted(groups.items()):
        valid = [r for r in rs if r["valid"]]
        prim = sum(1 for r in valid if r["primary"])
        rows.append(
            {
                "condition": cond,
                "family": fam,
                "lang": lang,
                "n": len(rs),
                "n_valid": len(valid),
                "primary_rate": prim / len(valid) if valid else float("nan"),
                "invalid_rate": 1 - len(valid) / len(rs),
            }
        )
    return rows
