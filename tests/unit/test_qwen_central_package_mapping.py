from __future__ import annotations

from datetime import datetime

import pytest

from app.qwen.models import (
    QwenAnswerResult,
    QwenSource,
    QwenTaskRunResult,
)
from app.qwen.package.mapping import (
    answer_result_to_geo_answer,
    answer_result_to_geo_sources,
    build_geo_answer_id,
    build_geo_task_id,
    qwen_mode_to_geo_mode,
    qwen_task_status_to_geo_status,
    task_run_to_geo_task,
)


def test_qwen_mode_maps_to_central_mode():
    assert (
        qwen_mode_to_geo_mode(
            "quick"
        )
        == "quick"
    )

    assert (
        qwen_mode_to_geo_mode(
            "research"
        )
        == "expert"
    )

    with pytest.raises(
        ValueError
    ):
        qwen_mode_to_geo_mode(
            "unknown"
        )


def test_qwen_status_maps_to_central_status():
    assert (
        qwen_task_status_to_geo_status(
            "pass"
        )
        == "success"
    )

    assert (
        qwen_task_status_to_geo_status(
            "fail"
        )
        == "failed"
    )

    assert (
        qwen_task_status_to_geo_status(
            "blocked"
        )
        == "failed"
    )

    assert (
        qwen_task_status_to_geo_status(
            "pending"
        )
        == "running"
    )


def test_geo_task_id_is_stable_and_batch_scoped():
    first = build_geo_task_id(
        batch_id="batch-001",
        question_id="Q001",
        mode="research",
    )

    repeated = build_geo_task_id(
        batch_id="batch-001",
        question_id="Q001",
        mode="research",
    )

    other_batch = build_geo_task_id(
        batch_id="batch-002",
        question_id="Q001",
        mode="research",
    )

    assert first == repeated
    assert first != other_batch


def test_task_maps_to_central_record():
    result = QwenTaskRunResult(
        question_id="Q001",
        question="测试问题",
        mode="research",
        status="blocked",
        error_type=(
            "QwenRiskControlError"
        ),
        error_message="模拟风控",
    )

    task = task_run_to_geo_task(
        result,
        batch_id="batch-001",
    )

    assert (
        task.mode_code
        == "expert"
    )

    assert (
        task.task_status
        == "failed"
    )

    assert (
        task.error_code
        == "QwenRiskControlError"
    )

    assert task.task_id.startswith(
        "qwen_task_"
    )


def test_answer_maps_to_central_record():
    acquired_at = datetime(
        2026,
        9,
        1,
        12,
        0,
    )

    result = QwenAnswerResult(
        question_id="Q001",
        question="测试问题",
        answer="  测试回答  ",
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
        sources=[
            QwenSource(
                rank=1,
                title="来源",
                url="https://example.com/1",
            )
        ],
        citation_mapping_available=False,
        acquired_at=acquired_at,
    )

    answer = answer_result_to_geo_answer(
        result,
        batch_id="batch-001",
    )

    expected_task_id = (
        build_geo_task_id(
            batch_id="batch-001",
            question_id="Q001",
            mode="research",
        )
    )

    assert (
        answer.task_id
        == expected_task_id
    )

    assert (
        answer.answer_id
        == build_geo_answer_id(
            task_id=expected_task_id
        )
    )

    assert (
        answer.mode_code
        == "expert"
    )

    assert (
        answer.answer_text_raw
        == "  测试回答  "
    )

    assert (
        answer.answer_text_clean
        == "测试回答"
    )

    assert (
        answer.acquisition_status
        == "success"
    )

    assert (
        answer.validation_status
        == "PASS"
    )

    assert answer.is_complete is True

    assert (
        answer.source_count_raw
        == 1
    )

    assert (
        answer.platform_meta_json[
            "original_mode"
        ]
        == "research"
    )

    assert (
        answer.platform_meta_json[
            "turn_id"
        ]
        == "turn-001"
    )


def test_sources_reference_answer_and_mark_duplicates():
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
        sources=[
            QwenSource(
                rank=1,
                title="来源一",
                url=(
                    "https://example.com/a"
                ),
            ),
            QwenSource(
                rank=2,
                title="来源一重复",
                url=(
                    "https://example.com/a"
                ),
            ),
        ],
    )

    records = (
        answer_result_to_geo_sources(
            result,
            batch_id="batch-001",
        )
    )

    assert len(records) == 2

    assert (
        records[0].answer_id
        == records[1].answer_id
    )

    assert (
        records[0].source_order
        == 1
    )

    assert (
        records[1].source_order
        == 2
    )

    assert (
        records[0].source_url_raw
        == "https://example.com/a"
    )

    assert (
        records[0].is_duplicate_in_answer
        is False
    )

    assert (
        records[1].is_duplicate_in_answer
        is True
    )

    assert (
        records[0].occurrence_id
        != records[1].occurrence_id
    )
