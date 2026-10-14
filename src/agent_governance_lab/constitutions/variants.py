"""Generate wording variants of the fourth ("Boundless Care") axiom section.

Only two things vary: the section *heading* term and the *body* term. Everything outside the
section is left byte-identical. Generation fails loudly (``VariantError``) if the section
cannot be found or a required substitution matches nothing, so a silently unchanged variant
can never enter a run.

The condition ids follow the design document: C1 is the paper's wording (heading Care,
body compassion); the frozen table lives in the pre-registration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

BOUNDARY_CLAUSE = {
    "en": "Never relieve suffering by deceiving people or by overriding their own wishes.",
    "zh": "不得以欺骗或越过当事人意愿的方式缓解痛苦。",
}


class VariantError(ValueError):
    """The input text does not have the structure the variant needs."""


@dataclass(frozen=True)
class Variant:
    vid: str
    lang: str  # "en" | "zh"
    heading: str  # "care" | "compassion" | "none"
    body: str  # "care" | "compassion" | "keep"
    extra: bool = False  # append the boundary clause to the section (H5)


VARIANTS: dict[str, Variant] = {
    v.vid: v
    for v in (
        # reference arm: heading "Care", body "compassion" (the paper's wording)
        Variant("C1", "en", "care", "compassion"),
        Variant("C2", "en", "compassion", "compassion"),
        Variant("C3", "en", "care", "care"),
        Variant("C4", "en", "compassion", "care"),
        # H5 only: paper wording plus one boundary sentence
        Variant("E1", "en", "care", "compassion", extra=True),
        Variant("C5", "zh", "care", "compassion"),
        Variant("C6", "zh", "compassion", "compassion"),
        Variant("C7", "zh", "care", "care"),
        Variant("C8", "zh", "compassion", "care"),
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


# Plain label line such as "Boundless Care:" (the upstream axioms file uses this form).
_LABEL_RE = re.compile(r"^([^\s#>\-*\"'][^:：\n]*?)([:：])\s*$")


def _is_key_line(line: str) -> bool:
    m = _HEADING_RE.match(line)
    if m:
        return bool(_SECTION_KEY.search(m.group(2)))
    m = _LABEL_RE.match(line)
    return bool(m and _SECTION_KEY.search(m.group(1)))


def _find_section(lines: list[str]) -> tuple[int, int]:
    start = next((i for i, line in enumerate(lines) if _is_key_line(line)), -1)
    if start < 0:
        raise VariantError("no 'Boundless Care/Compassion' (or 无量慈悲/无量关怀) heading found")
    head = _HEADING_RE.match(lines[start])
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if head:
            m = _HEADING_RE.match(lines[j])
            if m and len(m.group(1)) <= len(head.group(1)):
                end = j
                break
        elif _LABEL_RE.match(lines[j]):
            end = j
            break
    return start, end


def _retitle(title: str, lang: str, heading: str) -> str:
    if lang == "zh":
        # zh headings drop English parentheticals so the English term cannot leak into the zh arm
        title = re.sub(r"\s*[（(][^）)]*[）)]", "", title).strip()
        word = {"care": "无量关怀", "compassion": "无量慈悲", "none": "公理四"}[heading]
        return re.sub(r"无量(慈悲|关怀)", word, title)
    word = {"care": "Boundless Care", "compassion": "Boundless Compassion", "none": "Axiom 4"}[
        heading
    ]
    return re.sub(r"Boundless\s+(Care|Compassion)", word, title, flags=re.IGNORECASE)


def _new_heading(old: str, lang: str, heading: str) -> str:
    m = _HEADING_RE.match(old)
    if m:
        return f"{m.group(1)} {_retitle(m.group(2), lang, heading)}"
    lm = _LABEL_RE.match(old)
    assert lm is not None
    return f"{_retitle(lm.group(1), lang, heading)}{lm.group(2)}"


def _append_clause(body: str, clause: str) -> str:
    """Add ``clause`` after the last non-empty line, copying that line's bullet style."""
    rows = body.split("\n")
    last = max((i for i, r in enumerate(rows) if r.strip()), default=-1)
    if last < 0:
        return clause
    prev = rows[last]
    if prev.startswith('- "'):
        new = f'- "{clause}"'
    elif prev.startswith("- "):
        new = f"- {clause}"
    else:
        new = clause
    rows.insert(last + 1, new)
    return "\n".join(rows)


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
    if v.extra:
        body = _append_clause(body, BOUNDARY_CLAUSE[v.lang])
    return "\n".join(
        [*lines[: start + 1], *([body] if body or end > start + 1 else []), *lines[end:]]
    )
