from __future__ import annotations

from app.qwen.analysis.validity import (
    is_valid_analysis_answer,
)
from app.qwen.models import (
    QwenAnswerResult,
    QwenTaskRunResult,
)


def make_task(
        status: str,
) -> QwenTaskRunResult:
    return QwenTaskRunResult(
        question_id="Q001",
        mode="quick",
        question="测试问题",
        status=status,
    )


def make_answer(
        answer: str,
) -> QwenAnswerResult:
    return QwenAnswerResult(
        question="测试问题",
        answer=answer,
        turn_id="turn-001",
        chat_url="https://www.qianwen.com/chat/test",
        mode="quick",
        mode_label="快速",
        question_id="Q001",
    )


def test_pass_with_non_empty_answer_is_valid() -> None:
    task = make_task("pass")
    answer = make_answer(
        "鸿茅药酒属于甲类非处方药。"
    )

    assert (
            is_valid_analysis_answer(
                task,
                answer,
            )
            is True
    )


def test_fail_task_is_invalid() -> None:
    task = make_task("fail")
    answer = make_answer(
        "鸿茅药酒属于甲类非处方药。"
    )

    assert (
            is_valid_analysis_answer(
                task,
                answer,
            )
            is False
    )


def test_blocked_task_is_invalid() -> None:
    task = make_task("blocked")
    answer = make_answer(
        "鸿茅药酒属于甲类非处方药。"
    )

    assert (
            is_valid_analysis_answer(
                task,
                answer,
            )
            is False
    )


def test_missing_answer_is_invalid() -> None:
    task = make_task("pass")

    assert (
            is_valid_analysis_answer(
                task,
                None,
            )
            is False
    )


def test_empty_answer_is_invalid() -> None:
    task = make_task("pass")
    answer = make_answer("")

    assert (
            is_valid_analysis_answer(
                task,
                answer,
            )
            is False
    )


def test_whitespace_answer_is_invalid() -> None:
    task = make_task("pass")
    answer = make_answer(
        "   \n\t   "
    )

    assert (
            is_valid_analysis_answer(
                task,
                answer,
            )
            is False
    )


def test_normal_answer_containing_refusal_words_is_still_valid() -> None:
    task = make_task("pass")
    answer = make_answer(
        "部分问题可能无法回答，但鸿茅药酒属于药品。"
    )

    assert (
            is_valid_analysis_answer(
                task,
                answer,
            )
            is True
    )


def test_known_qwen_refusal_is_invalid() -> None:
    task = make_task("pass")
    answer = make_answer(
        "你好，我无法回答这个问题，我们换一个话题聊聊吧。"
    )

    assert (
            is_valid_analysis_answer(
                task,
                answer,
            )
            is False
    )


def test_qwen_refusal_is_invalid() -> None:
    task = make_task("pass")
    answer = make_answer(
        "你好，我无法回答这个问题，我们换一个话题聊聊吧。"
    )

    assert (
            is_valid_analysis_answer(
                task,
                answer,
            )
            is False
    )
