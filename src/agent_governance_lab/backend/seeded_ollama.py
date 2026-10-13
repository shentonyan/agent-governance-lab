"""Seeded, ledgered Ollama backend.

Matches the ``generate(prompt, system, num_predict, format)`` shape of the upstream
``LLMBackend`` protocol without importing upstream code. Differences from a plain client:

* every call carries an explicit seed derived from (base seed, call index, prompt);
* every call is appended to a :class:`~agent_governance_lab.ledger.Ledger`;
* only loopback hosts are accepted, and environment proxies are ignored
  (a system proxy must never see prompts).

Seeding makes runs repeatable on the same model build and hardware; it is not a guarantee
across GPUs or Ollama versions. M0 measures this rather than assuming it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

import requests

from agent_governance_lab.ledger import Ledger

PostFn = Callable[[str, dict[str, Any], float], dict[str, Any]]

_LOOPBACK = {"localhost", "127.0.0.1", "::1"}


def _default_post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    with requests.Session() as session:
        session.trust_env = False  # ignore HTTP(S)_PROXY / system proxy
        resp = session.post(url, json=body, timeout=timeout)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data


def derive_seed(base_seed: int, call_index: int, prompt: str) -> int:
    h = hashlib.sha256(f"{base_seed}:{call_index}:{prompt}".encode()).digest()
    return int.from_bytes(h[:4], "big") & 0x7FFFFFFF


def assert_loopback(base_url: str) -> None:
    host = urlparse(base_url).hostname
    if host not in _LOOPBACK:
        raise ValueError(f"only loopback hosts are allowed, got {host!r}")


class SeededOllamaBackend:
    def __init__(
        self,
        model: str,
        ledger: Ledger,
        base_seed: int = 0,
        base_url: str = "http://127.0.0.1:11434",
        temperature: float = 1.0,
        top_p: float = 0.95,
        top_k: int = 20,
        num_ctx: int = 32768,
        timeout: float = 300.0,
        post: PostFn | None = None,
    ) -> None:
        assert_loopback(base_url)
        self.model = model
        self.ledger = ledger
        self.base_seed = base_seed
        self.base_url = base_url.rstrip("/")
        self.options: dict[str, Any] = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "num_ctx": num_ctx,
        }
        self.timeout = timeout
        self._post: PostFn = post or _default_post
        self.calls = 0

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        num_predict: int = 300,
        format: dict[str, Any] | None = None,  # noqa: A002 - mirrors the upstream protocol
    ) -> str | None:
        seed = derive_seed(self.base_seed, self.calls, prompt)
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {**self.options, "num_predict": num_predict, "seed": seed},
        }
        if system:
            body["system"] = system
        if format is not None:
            body["format"] = format
        data = self._post(f"{self.base_url}/api/generate", body, self.timeout)
        text = data.get("response")
        out = text if isinstance(text, str) else None
        self.ledger.append(
            "llm_call",
            {
                "index": self.calls,
                "model": self.model,
                "seed": seed,
                "options": body["options"],
                "system": system,
                "prompt": prompt,
                "format": format,
                "response": out,
                "response_sha256": hashlib.sha256((out or "").encode()).hexdigest(),
            },
        )
        self.calls += 1
        return out
