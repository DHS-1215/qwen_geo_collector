from __future__ import annotations

from typing import Literal

from app.qwen.analysis.mention_aggregator import (
    analyze_batch_mentions,
)
from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.models import (
    QwenAnswerResult,
    QwenTaskRunResult,
)


TaskStatus = Literal[
    "pass",
    "fail",
    "blocked",
]


def make_task(
    question_id: str,
    mode: str,
    status: TaskStatus = "pass",
) -> QwenTaskRunResult:
    return QwenTaskRunResult(
        question_id=question_id,
        mode=mode,
        question="测试问题",
        status=status,
    )


def make_answer(
    question_id: str,
    mode: str,
    answer: str,
) -> QwenAnswerResult:
    return QwenAnswerResult(
        question="测试问题",
        answer=answer,
        turn_id=f"{question_id}-{mode}",
        chat_url=(
            "https://www.qianwen.com/chat/test"
        ),
        mode=mode,
        mode_label=(
            "快速"
            if mode == "quick"
            else "思考研究"
        ),
        question_id=question_id,
    )


TARGET = MentionTarget(
    target_id="hongmao",
    aliases=["鸿茅药酒"],
)


def test_quick_mention_rate_is_one_half() -> None:
    items = [
        (
            make_task("Q001", "quick"),
            make_answer(
                "Q001",
                "quick",
                "鸿茅药酒属于药品。",
            ),
        ),
        (
            make_task("Q002", "quick"),
            make_answer(
                "Q002",
                "quick",
                "这是一段无关回答。",
            ),
        ),
    ]

    result = analyze_batch_mentions(
        items,
        [TARGET],
    )

    summary = result.summaries[
        "hongmao"
    ].quick

    assert summary.valid_count == 2
    assert summary.mentioned_count == 1
    assert summary.mention_rate == 0.5


def test_research_is_calculated_separately() -> None:
    items = [
        (
            make_task(
                "Q001",
                "research",
            ),
            make_answer(
                "Q001",
                "research",
                "鸿茅药酒被提及。",
            ),
        ),
    ]

    result = analyze_batch_mentions(
        items,
        [TARGET],
    )

    summary = result.summaries[
        "hongmao"
    ].research

    assert summary.valid_count == 1
    assert summary.mentioned_count == 1
    assert summary.mention_rate == 1.0


def test_all_answers_combines_modes() -> None:
    items = [
        (
            make_task("Q001", "quick"),
            make_answer(
                "Q001",
                "quick",
                "未提及目标产品。",
            ),
        ),
        (
            make_task(
                "Q001",
                "research",
            ),
            make_answer(
                "Q001",
                "research",
                "鸿茅药酒被提及。",
            ),
        ),
        (
            make_task("Q002", "quick"),
            make_answer(
                "Q002",
                "quick",
                "仍然没有提及。",
            ),
        ),
    ]

    result = analyze_batch_mentions(
        items,
        [TARGET],
    )

    summary = result.summaries[
        "hongmao"
    ].all_answers

    assert summary.valid_count == 3
    assert summary.mentioned_count == 1
    assert summary.mention_rate == (
        1 / 3
    )


def test_invalid_answers_do_not_enter_denominator() -> None:
    items = [
        (
            make_task("Q001", "quick"),
            make_answer(
                "Q001",
                "quick",
                "鸿茅药酒被提及。",
            ),
        ),
        (
            make_task(
                "Q002",
                "quick",
                status="fail",
            ),
            make_answer(
                "Q002",
                "quick",
                "鸿茅药酒被提及。",
            ),
        ),
        (
            make_task(
                "Q003",
                "quick",
                status="blocked",
            ),
            make_answer(
                "Q003",
                "quick",
                "鸿茅药酒被提及。",
            ),
        ),
    ]

    result = analyze_batch_mentions(
        items,
        [TARGET],
    )

    summary = result.summaries[
        "hongmao"
    ].quick

    assert summary.valid_count == 1
    assert summary.mentioned_count == 1
    assert summary.mention_rate == 1.0


def test_question_level_merges_quick_and_research() -> None:
    items = [
        (
            make_task("Q001", "quick"),
            make_answer(
                "Q001",
                "quick",
                "没有提及。",
            ),
        ),
        (
            make_task(
                "Q001",
                "research",
            ),
            make_answer(
                "Q001",
                "research",
                "鸿茅药酒被提及。",
            ),
        ),
        (
            make_task("Q002", "quick"),
            make_answer(
                "Q002",
                "quick",
                "没有提及。",
            ),
        ),
        (
            make_task(
                "Q002",
                "research",
                status="fail",
            ),
            None,
        ),
    ]

    result = analyze_batch_mentions(
        items,
        [TARGET],
    )

    summary = result.summaries[
        "hongmao"
    ].question_level

    assert summary.valid_count == 2
    assert summary.mentioned_count == 1
    assert summary.mention_rate == 0.5


def test_zero_valid_answers_returns_zero_rate() -> None:
    items = [
        (
            make_task(
                "Q001",
                "quick",
                status="fail",
            ),
            None,
        ),
    ]

    result = analyze_batch_mentions(
        items,
        [TARGET],
    )

    summary = result.summaries[
        "hongmao"
    ]

    assert summary.quick.valid_count == 0
    assert summary.quick.mention_rate == 0.0

    assert (
        summary.research.valid_count
        == 0
    )
    assert (
        summary.research.mention_rate
        == 0.0
    )

    assert (
        summary.all_answers.valid_count
        == 0
    )
    assert (
        summary.all_answers.mention_rate
        == 0.0
    )

    assert (
        summary.question_level.valid_count
        == 0
    )
    assert (
        summary.question_level.mention_rate
        == 0.0
    )
