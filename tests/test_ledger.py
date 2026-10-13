from pathlib import Path

import pytest

from agent_governance_lab.ledger import Ledger, verify_ledger


def test_chain_ok_and_resumes(tmp_path: Path) -> None:
    p = tmp_path / "l.jsonl"
    led = Ledger(p)
    led.append("a", {"x": 1})
    led.append("b", {"y": "z"})
    assert verify_ledger(p).entries == 2
    led2 = Ledger(p)
    led2.append("c", {})
    rep = verify_ledger(p)
    assert rep.ok and rep.entries == 3


def test_tamper_detected(tmp_path: Path) -> None:
    p = tmp_path / "l.jsonl"
    led = Ledger(p)
    led.append("a", {"x": 1})
    led.append("b", {"x": 2})
    p.write_text(p.read_text(encoding="utf-8").replace('"x":1', '"x":9'), encoding="utf-8")
    rep = verify_ledger(p)
    assert not rep.ok and "hash mismatch" in rep.error


def test_deleted_line_detected(tmp_path: Path) -> None:
    p = tmp_path / "l.jsonl"
    led = Ledger(p)
    for i in range(3):
        led.append("k", {"i": i})
    lines = p.read_text(encoding="utf-8").splitlines()
    p.write_text("\n".join([lines[0], lines[2]]) + "\n", encoding="utf-8")
    assert not verify_ledger(p).ok


def test_refuses_to_extend_corrupt(tmp_path: Path) -> None:
    p = tmp_path / "l.jsonl"
    p.write_text("not json\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Ledger(p)


def test_missing_file_reported(tmp_path: Path) -> None:
    assert not verify_ledger(tmp_path / "nope.jsonl").ok
