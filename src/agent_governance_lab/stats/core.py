"""Small, dependency-light statistics used by the pre-registered analyses."""

from __future__ import annotations

import math
from collections.abc import Hashable, Sequence
from dataclasses import dataclass

import numpy as np


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("need 0 <= k <= n and n > 0")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from discordant counts b and c."""
    if b < 0 or c < 0:
        raise ValueError("counts must be non-negative")
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = float(sum(math.comb(n, i) for i in range(k + 1))) / 2**n
    return float(min(1.0, 2 * tail))


def holm(pvalues: Sequence[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, returned in the input order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvalues[idx])
        adjusted[idx] = min(1.0, running)
    return adjusted


def phi(x: Sequence[int], y: Sequence[int]) -> float:
    """Phi coefficient of two binary sequences; NaN if either is constant."""
    if len(x) != len(y) or not x:
        raise ValueError("sequences must be non-empty and equal length")
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


@dataclass(frozen=True)
class BootstrapResult:
    mean_diff: float
    lo: float
    hi: float
    n_items: int
    n_clusters: int


def cluster_bootstrap_diff(
    a: Sequence[float],
    b: Sequence[float],
    clusters: Sequence[Hashable],
    n_boot: int = 10_000,
    seed: int = 0,
    alpha: float = 0.05,
) -> BootstrapResult:
    """Paired difference (a - b) with a percentile CI from resampling whole clusters.

    Items sharing a cluster (e.g. variants of one scenario) are resampled together, so the
    interval does not pretend they are independent.
    """
    if not (len(a) == len(b) == len(clusters)) or not a:
        raise ValueError("a, b, clusters must be non-empty and equal length")
    diff = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    groups: dict[Hashable, list[float]] = {}
    for d, c in zip(diff, clusters, strict=True):
        groups.setdefault(c, []).append(float(d))
    sums = np.array([sum(v) for v in groups.values()])
    sizes = np.array([len(v) for v in groups.values()])
    rng = np.random.default_rng(seed)
    k = len(groups)
    idx = rng.integers(0, k, size=(n_boot, k))
    boot = sums[idx].sum(axis=1) / sizes[idx].sum(axis=1)
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    return BootstrapResult(float(diff.mean()), float(lo), float(hi), len(diff), k)


def equivalent(lo: float, hi: float, margin: float) -> bool:
    """CI-inclusion equivalence: the whole interval lies inside (-margin, +margin)."""
    if margin <= 0:
        raise ValueError("margin must be positive")
    return -margin < lo and hi < margin
