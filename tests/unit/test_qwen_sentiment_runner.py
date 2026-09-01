from __future__ import annotations

import asyncio

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment_runner import (
    analyze_batch_sentiment,
)
from app.qwen.models import (
    QwenAnswerResult,
    QwenTaskRunResult,
)


REFUSAL_TEXT = (
    "你好，我无法回答这个问题，"
    "我们换一个话题聊聊吧。"
)


class MappingClassifier:
    name = "mapping-classifier"

    def __init__(
        self,
        labels: dict[str, str],
    ) -> None:
        self.labels = labels
        self.calls: list[str] = []

    async def classify(
        self,
        *,
        answer_text: str,
        target: MentionTarget,
    ) -> str:
        self.calls.append(
            answer_text
        )

        return self.labels[
            answer_text
        ]


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao",
        aliases=[
            "鸿茅药酒",
        ],
    )


def _item(
    *,
    question_id: str,
    mode: str,
    answer: str | None,
    status: str = "pass",
):
    task_result = QwenTaskRunResult(
        question_id=question_id,
        mode=mode,
        question="测试问题",
        status=status,
        output_path=(
            f"{question_id}_{mode}.json"
        ),
    )

    if answer is None:
        return (
            task_result,
            None,
        )

    answer_result = QwenAnswerResult(
        question_id=question_id,
        question="测试问题",
        answer=answer,
        turn_id="test-turn",
        chat_url=(
            "https://www.qianwen.com/chat/test"
        ),
        mode=mode,
        mode_label=(
            "快速"
            if mode == "quick"
            else "思考研究"
        ),
    )

    return (
        task_result,
        answer_result,
    )


def test_only_valid_mentioned_answer_is_classified():
    mentioned = (
        "鸿茅药酒属于正规药品。"
    )

    not_mentioned = (
        "这是一个普通回答。"
    )

    classifier = MappingClassifier(
        {
            mentioned: "neutral",
        }
    )

    result = asyncio.run(
        analyze_batch_sentiment(
            items=[
                _item(
                    question_id="Q001",
                    mode="quick",
                    answer=mentioned,
                ),
                _item(
                    question_id="Q002",
                    mode="quick",
                    answer=not_mentioned,
                ),
            ],
            targets=[
                _target()
            ],
            classifier=classifier,
        )
    )

    summary = result.summaries[
        "hongmao"
    ].quick

    assert classifier.calls == [
        mentioned
    ]

    assert (
        summary.planned_mention_count
        == 1
    )

    assert (
        summary.classified_mention_count
        == 1
    )

    assert summary.neutral_count == 1

    assert (
        summary.non_negative_rate
        == 1.0
    )


def test_refusal_is_not_classified():
    classifier = MappingClassifier(
        {}
    )

    result = asyncio.run(
        analyze_batch_sentiment(
            items=[
                _item(
                    question_id="Q001",
                    mode="quick",
                    answer=REFUSAL_TEXT,
                )
            ],
            targets=[
                _target()
            ],
            classifier=classifier,
        )
    )

    assert classifier.calls == []

    detail = result.details[0]

    assert (
        detail.classification_planned
        is False
    )

    assert (
        detail.sentiment_status
        == "not_applicable"
    )


def test_failed_task_is_not_classified():
    classifier = MappingClassifier(
        {}
    )

    result = asyncio.run(
        analyze_batch_sentiment(
            items=[
                _item(
                    question_id="Q001",
                    mode="quick",
                    answer=None,
                    status="fail",
                )
            ],
            targets=[
                _target()
            ],
            classifier=classifier,
        )
    )

    assert classifier.calls == []

    assert (
        result.details[0]
        .classification_planned
        is False
    )


def test_batch_applies_business_rule_and_question_priority():
    quick_answer = (
        "鸿茅药酒属于一种药品。"
    )

    research_answer = (
        "鸿茅药酒曾因违法广告"
        "引发较大争议。"
    )

    classifier = MappingClassifier(
        {
            quick_answer: "neutral",
            research_answer: "positive",
        }
    )

    result = asyncio.run(
        analyze_batch_sentiment(
            items=[
                _item(
                    question_id="Q001",
                    mode="quick",
                    answer=quick_answer,
                ),
                _item(
                    question_id="Q001",
                    mode="research",
                    answer=research_answer,
                ),
            ],
            targets=[
                _target()
            ],
            classifier=classifier,
        )
    )

    assert len(result.details) == 2

    research_detail = result.details[1]

    assert (
        research_detail.model_sentiment
        == "positive"
    )

    assert (
        research_detail.final_sentiment
        == "negative"
    )

    assert research_detail.rule_hit
    assert research_detail.rule_override

    summary = result.summaries[
        "hongmao"
    ]

    assert (
        summary.quick.neutral_count
        == 1
    )

    assert (
        summary.research.negative_count
        == 1
    )

    assert (
        summary.question_level
        .negative_count
        == 1
    )

    assert (
        summary.question_level
        .non_negative_rate
        == 0.0
    )


def test_duplicate_target_is_rejected():
    classifier = MappingClassifier(
        {}
    )

    try:
        asyncio.run(
            analyze_batch_sentiment(
                items=[],
                targets=[
                    _target(),
                    _target(),
                ],
                classifier=classifier,
            )
        )

    except ValueError as exc:
        assert (
            "duplicate sentiment target_id"
            in str(exc)
        )

    else:
        raise AssertionError(
            "expected ValueError"
        )
