"""M0 self-check: is the local Ollama usable and how deterministic is it?"""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from agent_governance_lab.backend.seeded_ollama import (
    PostFn,
    SeededOllamaBackend,
    assert_loopback,
)
from agent_governance_lab.ledger import Ledger

GetFn = Callable[[str, float], dict[str, Any]]


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _default_get(url: str, timeout: float) -> dict[str, Any]:
    with requests.Session() as session:
        session.trust_env = False
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data


def run_self_check(
    model: str,
    base_url: str = "http://127.0.0.1:11434",
    seed: int = 0,
    repeats: int = 3,
    get: GetFn | None = None,
    post: PostFn | None = None,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        assert_loopback(base_url)
    except ValueError as exc:
        return [CheckResult("loopback", False, str(exc))]
    results.append(CheckResult("loopback", True, urlparse(base_url).hostname or ""))

    getter = get or _default_get
    try:
        tags = getter(f"{base_url.rstrip('/')}/api/tags", 10.0)
    except Exception as exc:  # noqa: BLE001 - report any transport failure
        results.append(CheckResult("reachable", False, repr(exc)))
        return results
    results.append(CheckResult("reachable", True, "GET /api/tags"))

    names = {str(m.get("name", "")) for m in tags.get("models", [])}
    present = model in names or f"{model}:latest" in names
    results.append(CheckResult("model_present", present, model))
    if not present:
        return results

    with tempfile.TemporaryDirectory() as tmp:
        prompt = "List three prime numbers, comma separated."
        # same (seed, call-index, prompt) must give the same text: re-create the backend per repeat
        outs = []
        for _ in range(repeats):
            b = SeededOllamaBackend(
                model, Ledger(Path(tmp) / "r.jsonl"), base_seed=seed, base_url=base_url, post=post
            )
            outs.append(b.generate(prompt, num_predict=32))
        identical = len(set(outs)) == 1 and outs[0] is not None
        results.append(
            CheckResult("determinism", identical, f"{len(set(outs))} distinct of {repeats}")
        )
    return results
