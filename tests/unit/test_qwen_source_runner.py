from __future__ import annotations

from app.qwen.analysis.source_runner import (
    analyze_batch_sources,
)
from app.qwen.models import (
    QwenAnswerResult,
    QwenSource,
    QwenTaskRunResult,
)


REFUSAL_TEXT = (
    "你好，我无法回答这个问题，"
    "我们换一个话题聊聊吧。"
)


def _item(
    *,
    question_id: str,
    mode: str,
    answer: str | None,
    sources: list[
        QwenSource
    ] | None = None,
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
        sources=sources or [],
    )

    return (
        task_result,
        answer_result,
    )


def _source(
    *,
    rank: int,
    title: str,
    url: str,
) -> QwenSource:
    return QwenSource(
        rank=rank,
        title=title,
        url=url,
    )


def test_valid_answer_sources_are_analyzed():
    result = analyze_batch_sources(
        items=[
            _item(
                question_id="Q001",
                mode="quick",
                answer="正常回答",
                sources=[
                    _source(
                        rank=1,
                        title="人民网",
                        url=(
                            "https://www.people.com.cn/a"
                        ),
                    )
                ],
            )
        ]
    )

    assert (
        result.quick.total_occurrences
        == 1
    )

    assert (
        result.quick.unique_source_count
        == 1
    )

    item = result.quick.top_sources[0]

    assert (
        item.domain
        == "people.com.cn"
    )


def test_canonical_duplicate_in_same_answer_counts_once():
    result = analyze_batch_sources(
        items=[
            _item(
                question_id="Q001",
                mode="quick",
                answer="正常回答",
                sources=[
                    _source(
                        rank=1,
                        title="来源A",
                        url=(
                            "https://example.com/a"
                            "?id=1&utm_source=qwen"
                        ),
                    ),
                    _source(
                        rank=2,
                        title="来源A重复",
                        url=(
                            "https://example.com/a"
                            "?id=1"
                        ),
                    ),
                ],
            )
        ]
    )

    assert (
        result.quick.total_occurrences
        == 1
    )

    assert (
        result.quick.top_sources[0]
        .occurrence_count
        == 1
    )


def test_invalid_and_refusal_answers_are_excluded():
    result = analyze_batch_sources(
        items=[
            _item(
                question_id="Q001",
                mode="quick",
                answer=None,
                status="fail",
            ),
            _item(
                question_id="Q002",
                mode="quick",
                answer=REFUSAL_TEXT,
                sources=[
                    _source(
                        rank=1,
                        title="不应统计",
                        url=(
                            "https://example.com/a"
                        ),
                    )
                ],
            ),
        ]
    )

    assert (
        result.quick.total_occurrences
        == 0
    )

    assert (
        result.all_sources
        .total_occurrences
        == 0
    )


def test_quick_research_and_all_are_aggregated():
    source_url = (
        "https://example.com/a"
    )

    result = analyze_batch_sources(
        items=[
            _item(
                question_id="Q001",
                mode="quick",
                answer="快速回答",
                sources=[
                    _source(
                        rank=2,
                        title="来源A",
                        url=source_url,
                    )
                ],
            ),
            _item(
                question_id="Q001",
                mode="research",
                answer="研究回答",
                sources=[
                    _source(
                        rank=1,
                        title="来源A",
                        url=source_url,
                    )
                ],
            ),
        ]
    )

    assert (
        result.quick.total_occurrences
        == 1
    )

    assert (
        result.research
        .total_occurrences
        == 1
    )

    assert (
        result.all_sources
        .total_occurrences
        == 2
    )

    item = (
        result.all_sources
        .top_sources[0]
    )

    assert (
        item.occurrence_count
        == 2
    )

    assert (
        item.question_count
        == 1
    )

    assert (
        item.average_order
        == 1.5
    )
