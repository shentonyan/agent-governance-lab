import json
from pathlib import Path
from typing import Any

import pytest

from agent_governance_lab.exp01 import run_condition, summarize, system_prompt
from agent_governance_lab.probes import (
    CHOICE_SCHEMA,
    FAMILIES,
    ProbeError,
    build_prompt,
    is_primary,
    load_scenarios,
    option_order,
    parse_choice,
)

PILOT = Path(__file__).resolve().parent.parent / "data" / "probes" / "exp01_pilot.jsonl"


def test_pilot_file_is_valid_and_balanced() -> None:
    scenarios = load_scenarios(PILOT)
    assert len(scenarios) == 18
    for fam in FAMILIES:
        assert sum(1 for s in scenarios if s.family == fam) == 6


def test_order_is_deterministic_and_reversed() -> None:
    s = load_scenarios(PILOT)[0]
    o0, o1 = option_order(s, 0), option_order(s, 1)
    assert o0 == option_order(s, 0) and o1 == o0[::-1]
    assert sorted(o0) == sorted(FAMILIES[s.family][0])


def test_primary_class_positions_are_balanced() -> None:
    # across the pilot set, the primary option should not sit in one position only
    scenarios = load_scenarios(PILOT)
    letters = set()
    for s in scenarios:
        p = build_prompt(s, "en", 0)
        letters |= {k for k, c in p.letter_to_class.items() if is_primary(s.family, c)}
    assert len(letters) >= 3


def test_prompt_contains_all_options_in_both_languages() -> None:
    s = load_scenarios(PILOT)[3]
    for lang in ("en", "zh"):
        p = build_prompt(s, lang, 0)
        for letter, cls in p.letter_to_class.items():
            assert f"{letter}. {s.options[cls][lang]}" in p.text


def test_parse_choice() -> None:
    m = {"A": "X", "B": "Y", "C": "Z", "D": "W"}
    assert parse_choice('{"choice": "B"}', m) == ("B", "Y")
    for bad in (None, "", "B", '{"choice": "E"}', '{"x": 1}', "[1]"):
        assert parse_choice(bad, m) == (None, None)


def test_loader_rejects_bad_records(tmp_path: Path) -> None:
    good = PILOT.read_text(encoding="utf-8").splitlines()[0]
    rec: dict[str, Any] = json.loads(good)
    p = tmp_path / "s.jsonl"
    p.write_text(good + "\n" + good + "\n", encoding="utf-8")
    with pytest.raises(ProbeError, match="duplicate"):
        load_scenarios(p)
    del rec["options"]["REFUSE"]
    p.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    with pytest.raises(ProbeError, match="exactly"):
        load_scenarios(p)
    rec2 = json.loads(good)
    rec2["situation"]["zh"] = " "
    p.write_text(json.dumps(rec2) + "\n", encoding="utf-8")
    with pytest.raises(ProbeError, match="missing"):
        load_scenarios(p)
    p.write_text("not json\n", encoding="utf-8")
    with pytest.raises(ProbeError):
        load_scenarios(p)


class AlwaysFirstClass:
    """Fake backend that always picks the letter of one fixed class by reading the prompt."""

    def __init__(self, scenarios_by_prompt: dict[str, str], cls: str) -> None:
        self.map = scenarios_by_prompt
        self.cls = cls
        self.systems: list[str | None] = []
        self.formats: list[Any] = []

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        num_predict: int = 300,
        format: dict[str, Any] | None = None,  # noqa: A002
    ) -> str | None:
        self.systems.append(system)
        self.formats.append(format)
        return json.dumps({"choice": self.map[prompt]})


def test_run_condition_and_summary() -> None:
    scenarios = load_scenarios(PILOT)[:6]  # F1 only
    want = "COMFORT_FALSE"
    lookup: dict[str, str] = {}
    for s in scenarios:
        for order in (0, 1):
            for lang in ("en", "zh"):
                p = build_prompt(s, lang, order)
                lookup[p.text] = next(k for k, c in p.letter_to_class.items() if c == want)
    backend = AlwaysFirstClass(lookup, want)
    recs = run_condition("T", "AXIOMS", scenarios, ["en", "zh"], [0], [0, 1], lambda seed: backend)
    assert len(recs) == 6 * 2 * 2
    assert all(r["primary"] and r["valid"] for r in recs)
    assert all(f == CHOICE_SCHEMA for f in backend.formats)
    assert all(sy is not None and sy.endswith("AXIOMS") for sy in backend.systems)
    rows = summarize(recs)
    assert {r["lang"] for r in rows} == {"en", "zh"}
    assert all(r["primary_rate"] == 1.0 and r["invalid_rate"] == 0.0 for r in rows)


def test_invalid_outputs_are_counted_not_dropped() -> None:
    class Garbage:
        def generate(
            self,
            prompt: str,
            system: str | None = None,
            num_predict: int = 300,
            format: dict[str, Any] | None = None,  # noqa: A002
        ) -> str | None:
            return None

    scenarios = load_scenarios(PILOT)[:2]
    recs = run_condition("T", None, scenarios, ["en"], [0], [0], lambda seed: Garbage())
    assert len(recs) == 2 and not any(r["valid"] for r in recs)
    rows = summarize(recs)
    assert rows[0]["invalid_rate"] == 1.0 and rows[0]["n_valid"] == 0


def test_baseline_has_no_system_prompt() -> None:
    assert system_prompt(None, "en") is None
