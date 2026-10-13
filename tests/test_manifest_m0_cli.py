from pathlib import Path
from typing import Any

import pytest

from agent_governance_lab.cli import main
from agent_governance_lab.ledger import Ledger
from agent_governance_lab.m0 import run_self_check
from agent_governance_lab.manifest import scrub


def test_scrub_removes_identifying_strings() -> None:
    obj = {
        "path": "C:\\Users\\someone\\proj",
        "unix": "/home/alice/x",
        "mail": "a.b@example.org",
        "nested": ["/Users/bob/y", {"k": "host-1 ran"}],
    }
    out = scrub(obj, extra=("host-1",))
    flat = str(out)
    for bad in ("someone", "alice", "example.org", "bob", "host-1"):
        assert bad not in flat


def _get(models: list[str]) -> Any:
    def get(url: str, timeout: float) -> dict[str, Any]:
        return {"models": [{"name": m} for m in models]}

    return get


def _post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    return {"response": f"s{body['options']['seed']}"}


def test_self_check_pass() -> None:
    res = run_self_check("m", get=_get(["m:latest"]), post=_post)
    assert all(r.ok for r in res) and res[-1].name == "determinism"


def test_self_check_model_missing() -> None:
    res = run_self_check("m", get=_get(["other"]), post=_post)
    assert not res[-1].ok and res[-1].name == "model_present"


def test_self_check_detects_nondeterminism() -> None:
    n = {"i": 0}

    def post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        n["i"] += 1
        return {"response": str(n["i"])}

    res = run_self_check("m", get=_get(["m"]), post=post)
    assert not res[-1].ok


def test_self_check_rejects_remote() -> None:
    res = run_self_check("m", base_url="http://example.com", get=_get(["m"]), post=_post)
    assert not res[0].ok


def test_cli_verify_and_variants(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    led = Ledger(tmp_path / "l.jsonl")
    led.append("a", {})
    assert main(["verify-ledger", str(tmp_path / "l.jsonl")]) == 0
    (tmp_path / "l.jsonl").write_text("garbage\n", encoding="utf-8")
    assert main(["verify-ledger", str(tmp_path / "l.jsonl")]) == 1

    ax = tmp_path / "ax.md"
    ax.write_text("## 4. Boundless Care\nBe compassionate.\n", encoding="utf-8")
    assert (
        main(["make-variants", "--axioms", str(ax), "--lang", "en", "--out", str(tmp_path / "o")])
        == 0
    )
    assert (tmp_path / "o" / "C2.md").exists()
    ax.write_text("nothing\n", encoding="utf-8")
    assert (
        main(["make-variants", "--axioms", str(ax), "--lang", "en", "--out", str(tmp_path / "p")])
        == 1
    )
    capsys.readouterr()
