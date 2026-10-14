"""Experiment 1, path A: forced-choice behavior probes under a given system prompt."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol

from agent_governance_lab.probes import (
    CHOICE_SCHEMA,
    Scenario,
    build_prompt,
    is_primary,
    letter_distribution,
    parse_choice,
)
from agent_governance_lab.stats import cluster_bootstrap_diff, equivalent

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


def headroom(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sensitivity diagnostics per (condition, family, lang).

    For every (scenario, seed) the two option orders are compared: ``both`` = the primary class
    was chosen in both orders (content-driven), ``split`` = in exactly one order (consistent with
    a position preference), ``none`` = in neither. ``rate`` is the pooled primary-class share.
    """
    cells: dict[tuple[str, str, str], dict[tuple[str, int], dict[int, bool]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for r in records:
        if r["valid"]:
            cells[(r["condition"], r["family"], r["lang"])][(r["scenario"], r["seed"])][
                r["order"]
            ] = bool(r["primary"])
    rows: list[dict[str, Any]] = []
    for (cond, fam, lang), pairs in sorted(cells.items()):
        both = split = none = 0
        per_scen: dict[str, list[bool]] = defaultdict(list)
        total = prim = 0
        for (scen, _seed), by_order in pairs.items():
            for v in by_order.values():
                total += 1
                prim += v
                per_scen[scen].append(v)
            if len(by_order) == 2:
                k = sum(by_order.values())
                both += k == 2
                split += k == 1
                none += k == 0
        n_pairs = both + split + none
        inter = sum(1 for vs in per_scen.values() if 0.1 <= sum(vs) / len(vs) <= 0.9)
        rows.append(
            {
                "condition": cond,
                "family": fam,
                "lang": lang,
                "n_scenarios": len(per_scen),
                "rate": prim / total if total else float("nan"),
                "n_intermediate": inter,
                "both": both / n_pairs if n_pairs else float("nan"),
                "split": split / n_pairs if n_pairs else float("nan"),
                "none": none / n_pairs if n_pairs else float("nan"),
            }
        )
    return rows


class LogprobGenerator(Protocol):
    def generate_logprobs(
        self,
        prompt: str,
        system: str | None = None,
        num_predict: int = 20,
        format: dict[str, Any] | None = None,  # noqa: A002
        top_logprobs: int = 10,
    ) -> tuple[str | None, list[dict[str, Any]] | None]: ...


def run_condition_probs(
    condition: str,
    axioms_text: str | None,
    scenarios: Sequence[Scenario],
    langs: Sequence[str],
    orders: Sequence[int],
    backend: LogprobGenerator,
) -> list[dict[str, Any]]:
    """Probability readout: one call per (scenario, lang, order); no sampling noise."""
    records: list[dict[str, Any]] = []
    for lang in langs:
        system = system_prompt(axioms_text, lang)
        for s in scenarios:
            for order in orders:
                p = build_prompt(s, lang, order)
                _text, lp = backend.generate_logprobs(
                    p.text, system=system, num_predict=20, format=CHOICE_SCHEMA
                )
                dist = letter_distribution(lp)
                rec: dict[str, Any] = {
                    "condition": condition,
                    "scenario": s.sid,
                    "family": s.family,
                    "lang": lang,
                    "order": order,
                    "valid": dist is not None,
                    "probs": None,
                    "mass": None,
                }
                if dist is not None:
                    by_letter, mass = dist
                    rec["probs"] = {p.letter_to_class[k]: v for k, v in by_letter.items()}
                    rec["mass"] = mass
                records.append(rec)
    return records


def logodds_by_scenario(
    records: Sequence[dict[str, Any]],
    condition: str,
    lang: str,
    num: str,
    den: str,
    floor: float = 1e-6,
) -> dict[str, float]:
    """Mean over option orders of log(P(num)/P(den)) per scenario (cancels position bias)."""
    acc: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r["condition"] == condition and r["lang"] == lang and r["valid"]:
            pr = r["probs"]
            if num in pr and den in pr:
                acc[r["scenario"]].append(math.log(max(pr[num], floor) / max(pr[den], floor)))
    return {k: sum(v) / len(v) for k, v in acc.items()}


def compare_logodds(
    records: Sequence[dict[str, Any]],
    ref: str,
    cond: str,
    lang: str,
    num: str,
    den: str,
    margin: float,
    n_comparisons: int = 1,
    n_boot: int = 10_000,
    seed: int = 0,
) -> dict[str, Any]:
    """Paired scenario-level difference (cond - ref) in log-odds, Bonferroni-adjusted CI."""
    a = logodds_by_scenario(records, cond, lang, num, den)
    b = logodds_by_scenario(records, ref, lang, num, den)
    common = sorted(set(a) & set(b))
    if not common:
        raise ValueError("no scenarios in common between the two conditions")
    res = cluster_bootstrap_diff(
        [a[k] for k in common],
        [b[k] for k in common],
        common,
        n_boot=n_boot,
        seed=seed,
        alpha=0.05 / n_comparisons,
    )
    return {
        "ref": ref,
        "cond": cond,
        "lang": lang,
        "n": len(common),
        "diff": res.mean_diff,
        "lo": res.lo,
        "hi": res.hi,
        "margin": margin,
        "equivalent": equivalent(res.lo, res.hi, margin),
    }
