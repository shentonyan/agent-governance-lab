import pytest

from agent_governance_lab.constitutions.variants import VARIANTS, VariantError, make_variant

# Synthetic fixtures: invented wording, not a copy of any published axiom text.
EN = """# Axioms

## 1. Alpha
Alpha body.

## 4. Boundless Care
Act with compassion toward every party. Offer compassionate attention, never indifference.

## 5. Omega
Omega body mentions care of tools.
"""

ZH = """# 公理

## 1. 甲
甲正文。

## 4. 无量慈悲（Boundless Care）
对一切对象怀有慈悲,给予慈悲的关注。

## 5. 乙
乙正文,提到关怀工具。
"""

# Same layout as the upstream axioms file (plain "Label:" lines, quoted bullets); invented wording.
LABELS = """Alpha:
- "Alpha clause one."

Boundless Care:
- "Be gentle. Show compassionate concern for everyone."
- "Let compassion grow with ability."

Omega:
- "Omega mentions care of tools."
"""


def _section(text: str) -> str:
    return text.split("## 5.")[0].split("## 4.")[1] if "## 5." in text else text


def _body(text: str) -> str:
    return _section(text).split("\n", 1)[1]


def test_condition_table_matches_design_doc() -> None:
    expected = {
        "C1": ("en", "care", "compassion"),
        "C2": ("en", "compassion", "compassion"),
        "C3": ("en", "care", "care"),
        "C4": ("en", "compassion", "care"),
        "E1": ("en", "none", "keep"),
        "C5": ("zh", "care", "compassion"),
        "C6": ("zh", "compassion", "compassion"),
        "C7": ("zh", "care", "care"),
        "C8": ("zh", "compassion", "care"),
    }
    assert {k: (v.lang, v.heading, v.body) for k, v in VARIANTS.items()} == expected


def test_outside_section_is_byte_identical() -> None:
    for vid in ("C1", "C2", "C3", "C4", "E1"):
        out = make_variant(EN, vid)
        assert out.split("## 4.")[0] == EN.split("## 4.")[0]
        assert "## 5. Omega\nOmega body mentions care of tools." in out


def test_en_conditions() -> None:
    assert make_variant(EN, "C1") == EN  # reference arm reproduces the original wording
    c2 = make_variant(EN, "C2")
    assert "Boundless Compassion" in c2 and "compassion" in _body(c2)
    c3 = make_variant(EN, "C3")
    assert "## 4. Boundless Care" in c3 and "compassion" not in _body(c3).lower()
    assert "care" in _body(c3)
    c4 = make_variant(EN, "C4")
    assert "Boundless Compassion" in c4 and "compassion" not in _body(c4).lower()
    assert "Boundless" not in make_variant(EN, "E1")


def test_zh_heading_strips_english() -> None:
    c5 = make_variant(ZH, "C5")
    assert "无量关怀" in c5 and "Boundless" not in c5 and "慈悲" in _body(c5)
    c6 = make_variant(ZH, "C6")
    assert "无量慈悲" in c6 and "Boundless" not in c6
    c7 = make_variant(ZH, "C7")
    assert "无量关怀" in c7 and "慈悲" not in _body(c7) and "关怀" in _body(c7)
    c8 = make_variant(ZH, "C8")
    assert "无量慈悲" in c8 and "慈悲" not in _body(c8)
    assert "乙正文,提到关怀工具。" in c8


def test_fails_loudly() -> None:
    with pytest.raises(VariantError):
        make_variant("# nothing here\n", "C1")
    with pytest.raises(VariantError):
        make_variant("## 4. Boundless Care\nNo relevant words at all.\n", "C3")
    with pytest.raises(VariantError):
        make_variant(EN, "nope")


def test_all_variants_defined_for_both_langs() -> None:
    langs = {v.lang for v in VARIANTS.values()}
    assert langs == {"en", "zh"}
    for v in VARIANTS.values():
        make_variant(EN if v.lang == "en" else ZH, v.vid)


def test_label_style_section() -> None:
    assert make_variant(LABELS, "C1") == LABELS
    c3 = make_variant(LABELS, "C3")
    assert "Boundless Care:" in c3 and "compassion" not in c3.split("Omega:")[0].lower()
    assert "caring concern" in c3 and "Let care grow" in c3
    c4 = make_variant(LABELS, "C4")
    assert "Boundless Compassion:" in c4 and "caring concern" in c4
    e1 = make_variant(LABELS, "E1")
    assert "Axiom 4:" in e1 and "Boundless" not in e1
    for vid in ("C2", "C3", "C4", "E1"):
        out = make_variant(LABELS, vid)
        assert out.startswith(LABELS.split("Boundless")[0])
        assert out.endswith('- "Omega mentions care of tools."\n')
