from __future__ import annotations

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment_rules import (
    apply_negative_priority_rules,
)


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao",
        aliases=[
            "鸿茅药酒",
        ],
    )


def test_false_advertising_hits_negative():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "鸿茅药酒曾涉及虚假宣传问题。"
            ),
            target=_target(),
        )
    )

    assert result.rule_hit
    assert (
        result.final_sentiment
        == "negative"
    )

    assert (
        "false_advertising"
        in (result.reason or "")
    )


def test_illegal_advertising_hits_negative():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "鸿茅药酒曾出现违法广告问题。"
            ),
            target=_target(),
        )
    )

    assert result.rule_hit
    assert (
        result.final_sentiment
        == "negative"
    )


def test_historical_case_hits_negative():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "2018年的谭秦东事件"
                "曾引发较大社会争议。"
            ),
            target=_target(),
        )
    )

    assert result.rule_hit


def test_cross_province_case_hits_negative():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "相关事件曾涉及跨省抓捕。"
            ),
            target=_target(),
        )
    )

    assert result.rule_hit


def test_regulatory_penalty_hits_negative():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "相关广告曾受到行政处罚。"
            ),
            target=_target(),
        )
    )

    assert result.rule_hit


def test_rectification_hits_negative():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "监管部门曾要求责令整改。"
            ),
            target=_target(),
        )
    )

    assert result.rule_hit


def test_negated_false_advertising_is_suppressed():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "没有证据表明鸿茅药酒"
                "存在虚假宣传。"
            ),
            target=_target(),
        )
    )

    assert not result.rule_hit


def test_negated_penalty_is_suppressed():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "鸿茅药酒并未被处罚。"
            ),
            target=_target(),
        )
    )

    assert not result.rule_hit


def test_cannot_prove_is_suppressed():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "这些信息不能证明"
                "存在夸大宣传。"
            ),
            target=_target(),
        )
    )

    assert not result.rule_hit


def test_normal_answer_has_no_rule_hit():
    result = (
        apply_negative_priority_rules(
            answer_text=(
                "鸿茅药酒属于药品，"
                "应按照说明书合理使用。"
            ),
            target=_target(),
        )
    )

    assert not result.rule_hit


def test_other_target_does_not_use_hongmao_rules():
    target = MentionTarget(
        target_id="other",
        aliases=["其他品牌"],
    )

    result = (
        apply_negative_priority_rules(
            answer_text=(
                "其他品牌曾涉及虚假宣传。"
            ),
            target=target,
        )
    )

    assert not result.rule_hit
