from __future__ import annotations

from app.qwen.analysis.mention import (
    analyze_target,
    normalize_text,
)
from app.qwen.analysis.models import (
    MentionTarget,
)


def test_normalize_text() -> None:
    text = "ＡＢＣ　 鸿   茅 药 酒 "

    assert (
        normalize_text(text)
        == "abc 鸿 茅 药 酒"
    )


def test_analyze_target_matches_normal_alias() -> None:
    target = MentionTarget(
        target_id="hongmao",
        aliases=["鸿茅药酒"],
    )

    result = analyze_target(
        "鸿茅药酒属于甲类非处方药。",
        target,
    )

    assert result.mentioned is True
    assert result.mention_count == 1


def test_analyze_target_allows_spaces_between_chars() -> None:
    target = MentionTarget(
        target_id="hongmao",
        aliases=["鸿茅药酒"],
    )

    result = analyze_target(
        "这款产品叫鸿 茅 药 酒。",
        target,
    )

    assert result.mentioned is True
    assert result.mention_count == 1


def test_analyze_target_counts_multiple_mentions() -> None:
    target = MentionTarget(
        target_id="hongmao",
        aliases=["鸿茅药酒"],
    )

    result = analyze_target(
        (
            "鸿茅药酒属于药品。"
            "再次说明，鸿 茅 药 酒不是普通酒水。"
        ),
        target,
    )

    assert result.mentioned is True
    assert result.mention_count == 2


def test_analyze_target_is_case_insensitive() -> None:
    target = MentionTarget(
        target_id="demo",
        aliases=["HongMao"],
    )

    result = analyze_target(
        "HONGMAO is mentioned here.",
        target,
    )

    assert result.mentioned is True
    assert result.mention_count == 1


def test_analyze_target_returns_zero_when_not_mentioned() -> None:
    target = MentionTarget(
        target_id="hongmao",
        aliases=["鸿茅药酒"],
    )

    result = analyze_target(
        "这是一段完全无关的回答。",
        target,
    )

    assert result.mentioned is False
    assert result.mention_count == 0
