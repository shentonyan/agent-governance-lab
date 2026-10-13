import pytest

from agent_governance_lab.constitutions.variants import VARIANTS, VariantError, make_variant

# Synthetic fixture: invented wording, not a copy of any published axiom text.
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
对一切对象怀有慈悲，给予慈悲的关注。

## 5. 乙
乙正文，提到关怀工具。
"""


def _section(text: str) -> str:
    return text.split("## 5.")[0].split("## 4.")[1] if "## 5." in text else text


def test_outside_section_is_byte_identical() -> None:
    for vid in ("C1", "C2", "C3", "C4", "E1"):
        out = make_variant(EN, vid)
        assert out.split("## 4.")[0] == EN.split("## 4.")[0]
        assert "## 5. Omega\nOmega body mentions care of tools." in out


def test_en_conditions() -> None:
    c1 = make_variant(EN, "C1")
    assert "## 4. Boundless Care" in c1
    assert "compassion" not in _section(c1).lower().split("\n", 1)[1]
    assert "care" in _section(c1)
    c3 = make_variant(EN, "C3")
    assert "Boundless Compassion" in c3 and "compassion" not in _section(c3).split("\n", 1)[1]
    c2 = make_variant(EN, "C2")
    assert "Boundless Compassion" in c2 and "compassion" in _section(c2).split("\n", 1)[1]
    assert "Boundless" not in make_variant(EN, "E1")


def test_zh_heading_strips_english() -> None:
    c5 = make_variant(ZH, "C5")
    assert "无量慈悲" in c5 and "Boundless" not in c5
    c7 = make_variant(ZH, "C7")
    assert "无量慈悲" in c7 and "慈悲" not in _section(c7).split("\n", 1)[1]
    c6 = make_variant(ZH, "C6")
    assert "无量关怀" in c6 and "关怀" in _section(c6)
    assert "乙正文，提到关怀工具。" in c6


def test_fails_loudly() -> None:
    with pytest.raises(VariantError):
        make_variant("# nothing here\n", "C1")
    with pytest.raises(VariantError):
        make_variant("## 4. Boundless Care\nNo relevant words at all.\n", "C1")
    with pytest.raises(VariantError):
        make_variant(EN, "nope")


def test_all_variants_defined_for_both_langs() -> None:
    langs = {v.lang for v in VARIANTS.values()}
    assert langs == {"en", "zh"}
    for v in VARIANTS.values():
        make_variant(EN if v.lang == "en" else ZH, v.vid)
