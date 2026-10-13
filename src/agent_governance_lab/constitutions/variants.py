"""Generate wording variants of the fourth ("Boundless Care") axiom section.

Only two things vary: the section *heading* term and the *body* term. Everything outside the
section is left byte-identical. Generation fails loudly (``VariantError``) if the section
cannot be found or a required substitution matches nothing, so a silently unchanged variant
can never enter a run.

The condition table below is a draft; the frozen version lives in the pre-registration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


class VariantError(ValueError):
    """The input text does not have the structure the variant needs."""


@dataclass(frozen=True)
class Variant:
    vid: str
    lang: str  # "en" | "zh"
    heading: str  # "care" | "compassion" | "none"
    body: str  # "care" | "compassion" | "keep"


VARIANTS: dict[str, Variant] = {
    v.vid: v
    for v in (
        Variant("C1", "en", "care", "care"),
        Variant("C2", "en", "compassion", "compassion"),
        Variant("C3", "en", "compassion", "care"),
        Variant("C4", "en", "care", "compassion"),
        Variant("E1", "en", "none", "keep"),
        Variant("C5", "zh", "compassion", "compassion"),
        Variant("C6", "zh", "care", "care"),
        Variant("C7", "zh", "compassion", "care"),
        Variant("C8", "zh", "care", "compassion"),
    )
}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_SECTION_KEY = re.compile(r"Boundless\s+(Care|Compassion)|无量(慈悲|关怀)", re.IGNORECASE)

_EN_TO_COMPASSION = [(r"\bcaring\b", "compassionate"), (r"\bcare\b", "compassion")]
_EN_TO_CARE = [(r"\bcompassionate\b", "caring"), (r"\bcompassion\b", "care")]
_ZH_TO_COMPASSION = [("关怀", "慈悲")]
_ZH_TO_CARE = [("慈悲", "关怀")]


def _subst(text: str, rules: list[tuple[str, str]]) -> tuple[str, int]:
    total = 0
    for pat, repl in rules:

        def _keep_case(m: re.Match[str], repl: str = repl) -> str:
            s = m.group(0)
            return repl[0].upper() + repl[1:] if s[:1].isupper() else repl

        text, n = re.subn(pat, _keep_case, text, flags=re.IGNORECASE)
        total += n
    return text, total


def _find_section(lines: list[str]) -> tuple[int, int]:
    start = -1
    level = 0
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m and _SECTION_KEY.search(m.group(2)):
            start, level = i, len(m.group(1))
            break
    if start < 0:
        raise VariantError("no 'Boundless Care/Compassion' (or 无量慈悲/无量关怀) heading found")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = _HEADING_RE.match(lines[j])
        if m and len(m.group(1)) <= level:
            end = j
            break
    return start, end


def _new_heading(old: str, lang: str, heading: str) -> str:
    m = _HEADING_RE.match(old)
    assert m is not None
    hashes, title = m.group(1), m.group(2)
    if lang == "zh":
        # zh headings drop English parentheticals so the English term cannot leak into the zh arm
        title = re.sub(r"\s*[（(][^）)]*[）)]", "", title).strip()
        word = {"care": "无量关怀", "compassion": "无量慈悲", "none": "公理四"}[heading]
        title = re.sub(r"无量(慈悲|关怀)", word, title)
    else:
        word = {"care": "Boundless Care", "compassion": "Boundless Compassion", "none": "Axiom 4"}[
            heading
        ]
        title = re.sub(r"Boundless\s+(Care|Compassion)", word, title, flags=re.IGNORECASE)
    return f"{hashes} {title}"


def make_variant(text: str, vid: str) -> str:
    """Return ``text`` with the axiom-4 section rewritten according to variant ``vid``."""
    if vid not in VARIANTS:
        raise VariantError(f"unknown variant {vid!r}")
    v = VARIANTS[vid]
    lines = text.split("\n")
    start, end = _find_section(lines)
    lines[start] = _new_heading(lines[start], v.lang, v.heading)

    body = "\n".join(lines[start + 1 : end])
    if v.body != "keep":
        if v.lang == "en":
            rules = _EN_TO_COMPASSION if v.body == "compassion" else _EN_TO_CARE
            present = r"\bcompassion(ate)?\b" if v.body == "compassion" else r"\bcar(e|ing)\b"
        else:
            rules = _ZH_TO_COMPASSION if v.body == "compassion" else _ZH_TO_CARE
            present = "慈悲" if v.body == "compassion" else "关怀"
        body, n = _subst(body, rules)
        if n == 0 and not re.search(present, body, flags=re.IGNORECASE):
            raise VariantError(f"{vid}: body has neither source nor target term; refusing to emit")
    return "\n".join(
        [*lines[: start + 1], *([body] if body or end > start + 1 else []), *lines[end:]]
    )
