"""Scrub run manifests before they are committed or shared."""

from __future__ import annotations

import re
from typing import Any

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "<email>"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s\"']+", re.IGNORECASE), r"<home>"),
    (re.compile(r"/home/[^/\s\"']+"), "<home>"),
    (re.compile(r"/Users/[^/\s\"']+"), "<home>"),
]


def scrub_text(text: str, extra: tuple[str, ...] = ()) -> str:
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    for token in extra:
        if token:
            text = text.replace(token, "<redacted>")
    return text


def scrub(obj: Any, extra: tuple[str, ...] = ()) -> Any:
    """Recursively scrub strings (values and keys) in a JSON-like structure."""
    if isinstance(obj, str):
        return scrub_text(obj, extra)
    if isinstance(obj, dict):
        return {scrub_text(str(k), extra): scrub(v, extra) for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub(v, extra) for v in obj]
    return obj
