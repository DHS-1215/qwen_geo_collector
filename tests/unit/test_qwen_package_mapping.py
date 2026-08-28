from __future__ import annotations

import hashlib
from datetime import datetime

import pytest

from app.qwen.models import (
    QwenAnswerResult,
    QwenSource,
    QwenTaskRunResult,
)
from app.qwen.package.mapping import (
    answer_result_to_package_answer,
    answer_result_to_package_sources,
    build_source_occurrence_id,
    task_run_to_package_task,
)


def test_task_run_to_package_task() -> None:
    task_result = QwenTaskRunResult(
        question_id="Q001",
        question="测试问题",
        mode="quick",
        status="fail",
        error_type="RuntimeError",
        error_message="模拟失败",
    )

    package_task = (
        task_run_to_package_task(
            task_result
        )
    )

    assert (
            package_task.question_id
            == "Q001"
    )

    assert (
            package_task.question
            == "测试问题"
    )

    assert (
            package_task.mode
            == "quick"
    )

    assert (
            package_task.status
            == "fail"
    )

    assert (
            package_task.error_type
            == "RuntimeError"
    )

    assert (
            package_task.error_message
            == "模拟失败"
    )


def test_answer_result_to_package_answer() -> None:
    acquired_at = datetime(
        2026,
        8,
        28,
        11,
        45,
    )

    result = QwenAnswerResult(
        question_id="Q001",
        question="测试问题",
        answer="测试回答",
        turn_id="turn-001",
        chat_url=(
            "https://www.qianwen.com/"
            "chat/test"
        ),
        mode="research",
        mode_label="思考研究",
        search_queries=[
            "关键词1",
            "关键词2",
        ],
        citation_mapping_available=False,
        acquired_at=acquired_at,
    )

    package_answer = (
        answer_result_to_package_answer(
            result
        )
    )

    assert (
            package_answer.question_id
            == "Q001"
    )

    assert (
            package_answer.mode
            == "research"
    )

    assert (
            package_answer.answer
            == "测试回答"
    )

    assert (
            package_answer.search_queries
            == [
                "关键词1",
                "关键词2",
            ]
    )

    assert (
            package_answer.citation_mapping_available
            is False
    )

    assert (
            package_answer.acquired_at
            == acquired_at
    )


def test_answer_without_question_id_is_rejected() -> None:
    result = QwenAnswerResult(
        question="测试问题",
        answer="测试回答",
        turn_id="turn-001",
        chat_url=(
            "https://www.qianwen.com/"
            "chat/test"
        ),
        mode="quick",
        mode_label="快速",
    )

    with pytest.raises(
            ValueError,
            match="question_id",
    ):
        answer_result_to_package_answer(
            result
        )

    with pytest.raises(
            ValueError,
            match="question_id",
    ):
        answer_result_to_package_sources(
            result
        )


def test_quick_answer_has_no_package_sources() -> None:
    result = QwenAnswerResult(
        question_id="Q001",
        question="测试问题",
        answer="测试回答",
        turn_id="turn-001",
        chat_url=(
            "https://www.qianwen.com/"
            "chat/test"
        ),
        mode="quick",
        mode_label="快速",
        sources=[],
    )

    sources = (
        answer_result_to_package_sources(
            result
        )
    )

    assert sources == []


def test_research_sources_create_stable_occurrences() -> None:
    result = QwenAnswerResult(
        question_id="Q001",
        question="测试问题",
        answer="测试回答",
        turn_id="turn-001",
        chat_url=(
            "https://www.qianwen.com/"
            "chat/test"
        ),
        mode="research",
        mode_label="思考研究",
        sources=[
            QwenSource(
                rank=1,
                title="来源一",
                url=(
                    "https://example.com/"
                    "source-1"
                ),
            ),
            QwenSource(
                rank=2,
                title="来源二",
                url=(
                    "https://example.com/"
                    "source-2"
                ),
            ),
        ],
    )

    sources = (
        answer_result_to_package_sources(
            result
        )
    )

    assert len(sources) == 2

    assert (
            sources[0].question_id
            == "Q001"
    )

    assert (
            sources[0].mode
            == "research"
    )

    assert (
            sources[0].rank
            == 1
    )

    assert (
            sources[0].title
            == "来源一"
    )

    expected_raw = (
        "Q001|research|1|"
        "https://example.com/source-1"
    )

    expected_id = hashlib.sha1(
        expected_raw.encode(
            "utf-8"
        )
    ).hexdigest()[:12]

    assert (
            sources[0].occurrence_id
            == expected_id
    )

    # 同样输入必须生成稳定一致的 ID
    repeated_id = (
        build_source_occurrence_id(
            question_id="Q001",
            mode="research",
            rank=1,
            url=(
                "https://example.com/"
                "source-1"
            ),
        )
    )

    assert (
            repeated_id
            == expected_id
    )

    # rank 不同，应该是不同 occurrence
    assert (
            sources[0].occurrence_id
            != sources[1].occurrence_id
    )
