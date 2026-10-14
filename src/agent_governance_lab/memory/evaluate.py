"""Score a memory backend on a synthetic dataset (retrieval level, string matching)."""

from __future__ import annotations

import time
from typing import Any

from agent_governance_lab.memory.backends import Backend, make_backend
from agent_governance_lab.memory.datasets import Dataset
from agent_governance_lab.stats import wilson


def _pct(xs: list[float], q: float) -> float:
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))] if s else float("nan")


def evaluate(
    backend_id: str, ds: Dataset, k: int = 5, embed: Any = None, backend: Backend | None = None
) -> dict[str, Any]:
    be: Backend = backend if backend is not None else make_backend(backend_id, embed)
    t0 = time.perf_counter()
    for e in ds.writes:
        be.write(e)
    write_s = time.perf_counter() - t0
    fin = getattr(be, "finalize", None)
    t_fin = time.perf_counter()
    if callable(fin):
        fin()
    finalize_s = time.perf_counter() - t_fin

    per_kind: dict[str, dict[str, int]] = {}
    lat: list[float] = []
    rows: list[dict[str, Any]] = []
    for q in ds.queries:
        t1 = time.perf_counter()
        ctx = be.retrieve(q.text, k, q.as_of)
        lat.append(time.perf_counter() - t1)
        joined = "\n".join(ctx)
        hit = bool(q.truth) and q.truth in joined
        bad_any = any(f in joined for f in q.forbidden)
        top1_bad = bool(ctx) and any(f in ctx[0] for f in q.forbidden)
        top1_hit = bool(ctx) and bool(q.truth) and q.truth in ctx[0]
        d = per_kind.setdefault(
            q.kind, {"n": 0, "hit": 0, "top1_hit": 0, "stale_or_poison_only": 0, "top1_bad": 0}
        )
        d["n"] += 1
        d["hit"] += int(hit)
        d["top1_hit"] += int(top1_hit)
        d["stale_or_poison_only"] += int(bad_any and not hit)
        d["top1_bad"] += int(top1_bad)
        rows.append(
            {
                "qid": q.qid,
                "kind": q.kind,
                "hit": hit,
                "top1_hit": top1_hit,
                "bad_any": bad_any,
                "top1_bad": top1_bad,
            }
        )

    out: dict[str, Any] = {
        "dataset": ds.name,
        "backend": backend_id,
        "k": k,
        "n_writes": len(ds.writes),
        "write_seconds": write_s,
        "finalize_seconds": finalize_s,
        "query_p50_ms": _pct(lat, 0.5) * 1000,
        "query_p95_ms": _pct(lat, 0.95) * 1000,
        "kinds": {},
        "rows": rows,
    }
    for kind, d in per_kind.items():
        lo, hi = wilson(d["hit"], d["n"])
        out["kinds"][kind] = {
            **d,
            "hit_rate": d["hit"] / d["n"],
            "hit_lo": lo,
            "hit_hi": hi,
            "top1_hit_rate": d["top1_hit"] / d["n"],
        }
    return out
