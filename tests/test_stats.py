import math

import pytest

from agent_governance_lab.stats import (
    cluster_bootstrap_diff,
    equivalent,
    holm,
    mcnemar_exact,
    phi,
    wilson,
)


def test_wilson_known_value() -> None:
    lo, hi = wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3)
    assert hi == pytest.approx(0.7634, abs=1e-3)
    assert wilson(0, 10)[0] == 0.0 and wilson(10, 10)[1] == pytest.approx(1.0)


def test_wilson_bad_input() -> None:
    with pytest.raises(ValueError):
        wilson(3, 2)


def test_mcnemar() -> None:
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(5, 5) == 1.0
    assert mcnemar_exact(0, 10) == pytest.approx(2 / 1024)


def test_holm_matches_hand_computation() -> None:
    adj = holm([0.01, 0.04, 0.03])
    assert adj == pytest.approx([0.03, 0.06, 0.06])


def test_phi() -> None:
    assert phi([1, 0, 1, 0], [1, 0, 1, 0]) == pytest.approx(1.0)
    assert phi([1, 0, 1, 0], [0, 1, 0, 1]) == pytest.approx(-1.0)
    assert math.isnan(phi([1, 1, 1], [0, 1, 0]))


def test_bootstrap_detects_shift_and_is_reproducible() -> None:
    a = [1.0] * 40
    b = [0.0] * 40
    clusters = [i // 4 for i in range(40)]
    r1 = cluster_bootstrap_diff(a, b, clusters, n_boot=500, seed=1)
    r2 = cluster_bootstrap_diff(a, b, clusters, n_boot=500, seed=1)
    assert r1 == r2 and r1.mean_diff == 1.0 and r1.lo == 1.0 and r1.n_clusters == 10


def test_bootstrap_null_ci_covers_zero() -> None:
    a = [1.0, 0.0] * 20
    b = [0.0, 1.0] * 20
    r = cluster_bootstrap_diff(a, b, list(range(40)), n_boot=2000, seed=2)
    assert r.lo < 0 < r.hi


def test_equivalence() -> None:
    assert equivalent(-0.03, 0.04, 0.05)
    assert not equivalent(-0.03, 0.06, 0.05)
    with pytest.raises(ValueError):
        equivalent(0, 0, 0)
