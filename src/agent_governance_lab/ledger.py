"""Append-only, hash-chained JSONL ledger.

Each line is ``{"seq", "ts", "kind", "payload", "prev", "hash"}`` where ``hash`` is the
SHA-256 of the canonical JSON of every other field. Editing, deleting or reordering any line
breaks the chain and is reported by :func:`verify_ledger`.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(entry: dict[str, Any]) -> str:
    body = {k: entry[k] for k in ("seq", "ts", "kind", "payload", "prev")}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


class Ledger:
    """Append-only ledger bound to one file."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0
        self._prev = GENESIS
        if self.path.exists():
            report = verify_ledger(self.path)
            if not report.ok:
                raise ValueError(f"refusing to extend a corrupt ledger: {report.error}")
            self._seq = report.entries
            self._prev = report.last_hash

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "seq": self._seq,
            "ts": time.time(),
            "kind": kind,
            "payload": payload,
            "prev": self._prev,
        }
        entry["hash"] = _digest(entry)
        with self.path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(_canonical(entry) + "\n")
        self._seq += 1
        self._prev = str(entry["hash"])
        return entry


@dataclass(frozen=True)
class VerifyReport:
    ok: bool
    entries: int
    last_hash: str
    error: str = ""


def verify_ledger(path: Path) -> VerifyReport:
    """Re-compute the whole chain. Never raises on bad content; reports instead."""
    prev = GENESIS
    n = 0
    p = Path(path)
    if not p.exists():
        return VerifyReport(False, 0, prev, f"missing file: {p.name}")
    with p.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry["seq"] != n:
                    return VerifyReport(False, n, prev, f"line {lineno}: seq {entry['seq']} != {n}")
                if entry["prev"] != prev:
                    return VerifyReport(False, n, prev, f"line {lineno}: broken prev link")
                if _digest(entry) != entry["hash"]:
                    return VerifyReport(False, n, prev, f"line {lineno}: hash mismatch")
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                return VerifyReport(False, n, prev, f"line {lineno}: malformed ({exc!r})")
            prev = str(entry["hash"])
            n += 1
    return VerifyReport(True, n, prev)
