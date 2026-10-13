from pathlib import Path
from typing import Any

import pytest

from agent_governance_lab.backend.seeded_ollama import SeededOllamaBackend, derive_seed
from agent_governance_lab.ledger import Ledger, verify_ledger


class FakePost:
    def __init__(self) -> None:
        self.bodies: list[dict[str, Any]] = []

    def __call__(self, url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.bodies.append(body)
        return {"response": f"echo:{body['options']['seed']}"}


def test_seed_is_deterministic_and_call_dependent() -> None:
    assert derive_seed(1, 0, "p") == derive_seed(1, 0, "p")
    assert derive_seed(1, 0, "p") != derive_seed(1, 1, "p")
    assert derive_seed(1, 0, "p") != derive_seed(2, 0, "p")


def test_generate_logs_and_passes_seed(tmp_path: Path) -> None:
    post = FakePost()
    led = Ledger(tmp_path / "l.jsonl")
    b = SeededOllamaBackend("m", led, base_seed=7, post=post)
    out = b.generate("hello", system="sys", num_predict=5, format={"type": "object"})
    assert out == f"echo:{post.bodies[0]['options']['seed']}"
    body = post.bodies[0]
    assert body["system"] == "sys" and body["format"] == {"type": "object"}
    assert body["options"]["num_predict"] == 5 and body["think"] is False
    rep = verify_ledger(tmp_path / "l.jsonl")
    assert rep.ok and rep.entries == 1


def test_same_config_same_output(tmp_path: Path) -> None:
    outs = []
    for i in range(2):
        b = SeededOllamaBackend("m", Ledger(tmp_path / f"{i}.jsonl"), base_seed=3, post=FakePost())
        outs.append([b.generate("a"), b.generate("b")])
    assert outs[0] == outs[1]


@pytest.mark.parametrize("url", ["http://example.com:11434", "http://10.0.0.5:11434"])
def test_non_loopback_rejected(tmp_path: Path, url: str) -> None:
    with pytest.raises(ValueError):
        SeededOllamaBackend("m", Ledger(tmp_path / "l.jsonl"), base_url=url, post=FakePost())


def test_non_string_response_becomes_none(tmp_path: Path) -> None:
    def post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
        return {"error": "x"}

    b = SeededOllamaBackend("m", Ledger(tmp_path / "l.jsonl"), post=post)
    assert b.generate("p") is None
