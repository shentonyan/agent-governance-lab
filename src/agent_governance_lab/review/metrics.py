"""Metrics for the staged-review experiment."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Any

from agent_governance_lab.stats import mcnemar_exact, phi, wilson

BAD = ("C", "D")  # proposals that should be stopped
GOOD = ("A", "B")  # proposals that should pass


def read_results(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _rate(rows: Sequence[dict[str, Any]], pred: str) -> dict[str, Any]:
    n = len(rows)
    k = sum(1 for r in rows if r["final"] == pred)
    lo, hi = wilson(k, n) if n else (float("nan"), float("nan"))
    return {"k": k, "n": n, "rate": k / n if n else float("nan"), "lo": lo, "hi": hi}


def summarize(rows: Iterable[dict[str, Any]], split: str | None = None) -> dict[str, Any]:
    rs = [r for r in rows if split is None or r["split"] == split]
    by_cat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_sub: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rs:
        by_cat[r["category"]].append(r)
        by_sub[f"{r['category']}/{r['subtype']}"].append(r)
    bad = [r for r in rs if r["category"] in BAD]
    good = [r for r in rs if r["category"] in GOOD]
    return {
        "split": split or "all",
        "n": len(rs),
        "reject_by_category": {c: _rate(v, "reject") for c, v in sorted(by_cat.items())},
        "escalate_by_category": {c: _rate(v, "escalate") for c, v in sorted(by_cat.items())},
        "reject_by_subtype": {c: _rate(v, "reject") for c, v in sorted(by_sub.items())},
        "recall_bad": _rate(bad, "reject"),
        "false_reject_good": _rate(good, "reject"),
        "escalate_all": _rate(rs, "escalate"),
    }


def error_phi(rows: Iterable[dict[str, Any]], s1: str = "ethics", s2: str = "safety") -> float:
    """Phi of the two reviewers' errors (error = wrong side of the truth label)."""
    x: list[int] = []
    y: list[int] = []
    for r in rows:
        st = r["stages"]
        if s1 not in st or s2 not in st:
            continue
        bad = r["category"] in BAD
        for stage, out in ((s1, x), (s2, y)):
            v = st[stage]["verdict"]
            wrong = (v != "reject") if bad else (v == "reject")
            out.append(int(wrong))
    return phi(x, y) if x else float("nan")


def paired_mcnemar(
    a: Sequence[dict[str, Any]], b: Sequence[dict[str, Any]], categories: Sequence[str]
) -> dict[str, Any]:
    """Compare two arms on the same proposals: did the final verdict reject (1) or not (0)?"""
    ra = {r["pid"]: r for r in a if r["category"] in categories}
    rb = {r["pid"]: r for r in b if r["category"] in categories}
    common = sorted(set(ra) & set(rb))
    only_a = sum(1 for p in common if ra[p]["final"] == "reject" and rb[p]["final"] != "reject")
    only_b = sum(1 for p in common if rb[p]["final"] == "reject" and ra[p]["final"] != "reject")
    return {
        "n": len(common),
        "only_a": only_a,
        "only_b": only_b,
        "p": mcnemar_exact(only_a, only_b),
    }
