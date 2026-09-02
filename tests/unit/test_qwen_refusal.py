from __future__ import annotations

from app.qwen.refusal import (
    is_qwen_refusal,
)


def test_known_qwen_refusal_is_detected() -> None:
    answer = (
        "你好，我无法回答这个问题，"
        "我们换一个话题聊聊吧。"
    )

    assert (
        is_qwen_refusal(answer)
        is True
    )


def test_refusal_with_outer_whitespace_is_detected() -> None:
    answer = (
        "  \n你好，我无法回答这个问题，"
        "我们换一个话题聊聊吧。\n "
    )

    assert (
        is_qwen_refusal(answer)
        is True
    )


def test_normal_answer_is_not_refusal() -> None:
    answer = (
        "鸿茅药酒属于药品，"
        "相关信息可以结合公开资料核实。"
    )

    assert (
        is_qwen_refusal(answer)
        is False
    )


def test_normal_answer_containing_refusal_words_is_not_refusal() -> None:
    answer = (
        "有些问题模型可能无法回答，"
        "但鸿茅药酒的生产企业信息"
        "可以从公开资料中查询。"
    )

    assert (
        is_qwen_refusal(answer)
        is False
    )


def test_empty_answer_is_not_refusal() -> None:
    assert (
        is_qwen_refusal("")
        is False
    )
