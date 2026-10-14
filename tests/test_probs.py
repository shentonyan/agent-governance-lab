import math
from pathlib import Path
from typing import Any

import pytest

from agent_governance_lab.backend.seeded_ollama import SeededOllamaBackend
from agent_governance_lab.exp01 import compare_logodds, logodds_by_scenario, run_condition_probs
from agent_governance_lab.ledger import Ledger, verify_ledger
from agent_governance_lab.probes import build_prompt, letter_distribution, load_scenarios

PILOT = Path(__file__).resolve().parent.parent / "data" / "probes" / "exp01_pilot2.jsonl"


def _lp(letter_probs: dict[str, float]) -> list[dict[str, Any]]:
    tops = [{"token": k, "logprob": math.log(v)} for k, v in letter_probs.items()]
    return [
        {"token": '{"', "logprob": 0.0, "top_logprobs": [{"token": '{"', "logprob": 0.0}]},
        {"token": "A", "logprob": tops[0]["logprob"], "top_logprobs": tops},
    ]


def test_letter_distribution() -> None:
    dist = letter_distribution(_lp({"A": 0.6, "B": 0.2, "C": 0.1, "D": 0.05}))
    assert dist is not None
    probs, mass = dist
    assert mass == pytest.approx(0.95)
    assert sum(probs.values()) == pytest.approx(1.0)
    assert probs["A"] == pytest.approx(0.6 / 0.95)
    assert letter_distribution(None) is None
    assert letter_distribution([{"token": "x", "top_logprobs": []}]) is None


def test_letter_distribution_merges_variants() -> None:
    entry = {
        "token": "A",
        "top_logprobs": [
            {"token": "A", "logprob": math.log(0.3)},
            {"token": " A", "logprob": math.log(0.2)},
            {"token": "B", "logprob": math.log(0.5)},
        ],
    }
    dist = letter_distribution([entry])
    assert dist is not None and dist[0]["A"] == pytest.approx(0.5)


def test_backend_logprobs_roundtrip(tmp_path: Path) -> None:
    seen: dict[str, Any] = {}

    def post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        seen.update(body)
        return {"response": '{"choice": "A"}', "logprobs": _lp({"A": 0.7, "B": 0.3})}

    led = Ledger(tmp_path / "l.jsonl")
    b = SeededOllamaBackend("m", led, post=post)
    text, lp = b.generate_logprobs("p")
    assert text and lp and seen["logprobs"] is True and seen["top_logprobs"] == 10
    assert verify_ledger(tmp_path / "l.jsonl").ok


class FavourClass:
    """Fake backend: puts most probability on one class, optionally with a position bias."""

    def __init__(self, scenarios: list[Any], cls: str, strength: float) -> None:
        self.lookup: dict[str, dict[str, str]] = {}
        for s in scenarios:
            for lang in ("en", "zh"):
                for order in (0, 1):
                    p = build_prompt(s, lang, order)
                    self.lookup[p.text] = p.letter_to_class
        self.cls = cls
        self.strength = strength

    def generate_logprobs(
        self,
        prompt: str,
        system: str | None = None,
        num_predict: int = 20,
        format: dict[str, Any] | None = None,  # noqa: A002
        top_logprobs: int = 10,
    ) -> tuple[str | None, list[dict[str, Any]] | None]:
        mapping = self.lookup[prompt]
        probs = {}
        for letter, cls in mapping.items():
            probs[letter] = self.strength if cls == self.cls else (1 - self.strength) / 3
        return "{}", _lp(probs)


def test_probs_run_and_comparison() -> None:
    scenarios = [s for s in load_scenarios(PILOT) if s.family == "F1"]
    ref = run_condition_probs(
        "C1", None, scenarios, ["en"], [0, 1], FavourClass(scenarios, "COMFORT_FALSE", 0.10)
    )
    same = run_condition_probs(
        "C2", None, scenarios, ["en"], [0, 1], FavourClass(scenarios, "COMFORT_FALSE", 0.10)
    )
    up = run_condition_probs(
        "C3", None, scenarios, ["en"], [0, 1], FavourClass(scenarios, "COMFORT_FALSE", 0.40)
    )
    recs = ref + same + up
    assert all(r["valid"] for r in recs)
    lo = logodds_by_scenario(recs, "C1", "en", "COMFORT_FALSE", "HONEST_SUPPORT")
    assert set(lo) == {s.sid for s in scenarios}
    eq = compare_logodds(recs, "C1", "C2", "en", "COMFORT_FALSE", "HONEST_SUPPORT", 0.5, n_boot=500)
    assert eq["equivalent"] and eq["diff"] == pytest.approx(0.0, abs=1e-9)
    diff = compare_logodds(
        recs, "C1", "C3", "en", "COMFORT_FALSE", "HONEST_SUPPORT", 0.5, n_boot=500
    )
    assert not diff["equivalent"] and diff["diff"] > 1.0
    with pytest.raises(ValueError):
        compare_logodds(recs, "C1", "NOPE", "en", "COMFORT_FALSE", "HONEST_SUPPORT", 0.5)
