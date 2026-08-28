from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qwen.package.reader import (
    load_answer_result,
    load_batch_summary,
)


def test_load_batch_summary(
        tmp_path: Path,
) -> None:
    summary_path = (
            tmp_path
            / "batch_summary.json"
    )

    data = {
        "platform": "qwen",
        "status": "completed",
        "planned_count": 2,
        "executed_count": 2,
        "pass_count": 2,
        "fail_count": 0,
        "blocked_count": 0,
        "pending_count": 0,
        "task_results": [
            {
                "question_id": "Q001",
                "mode": "quick",
                "question": "测试问题1",
                "status": "pass",
                "output_path": (
                    "output/Q001_quick.json"
                ),
                "error_type": None,
                "error_message": None,
            },
            {
                "question_id": "Q001",
                "mode": "research",
                "question": "测试问题2",
                "status": "pass",
                "output_path": (
                    "output/Q001_research.json"
                ),
                "error_type": None,
                "error_message": None,
            },
        ],
        "started_at": (
            "2026-08-28T12:00:00"
        ),
        "finished_at": (
            "2026-08-28T12:05:00"
        ),
    }

    summary_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    summary = load_batch_summary(
        tmp_path
    )

    assert (
            summary.status
            == "completed"
    )

    assert (
            summary.planned_count
            == 2
    )

    assert (
            summary.pass_count
            == 2
    )

    assert (
            len(summary.task_results)
            == 2
    )

    assert (
            summary.task_results[0].question_id
            == "Q001"
    )

    assert (
            summary.task_results[1].mode
            == "research"
    )


def test_load_batch_summary_missing_file(
        tmp_path: Path,
) -> None:
    with pytest.raises(
            FileNotFoundError,
            match="batch summary not found",
    ):
        load_batch_summary(
            tmp_path
        )


def test_load_batch_summary_invalid_json(
        tmp_path: Path,
) -> None:
    summary_path = (
            tmp_path
            / "batch_summary.json"
    )

    summary_path.write_text(
        "{not valid json",
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match=(
                    "invalid batch summary JSON"
            ),
    ):
        load_batch_summary(
            tmp_path
        )


def test_load_answer_result(
        tmp_path: Path,
) -> None:
    answer_path = (
            tmp_path
            / "Q001_quick.json"
    )

    data = {
        "platform": "qwen",
        "question": "测试问题",
        "answer": "测试回答",
        "turn_id": "turn-001",
        "chat_url": (
            "https://www.qianwen.com/"
            "chat/test"
        ),
        "mode": "quick",
        "mode_label": "快速",
        "question_id": "Q001",
        "search_queries": [],
        "sources": [],
        "citation_mapping_available": False,
        "acquired_at": (
            "2026-08-28T12:10:00"
        ),
    }

    answer_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = load_answer_result(
        answer_path
    )

    assert (
            result.question_id
            == "Q001"
    )

    assert (
            result.mode
            == "quick"
    )

    assert (
            result.answer
            == "测试回答"
    )


def test_load_answer_result_missing_file(
        tmp_path: Path,
) -> None:
    with pytest.raises(
            FileNotFoundError,
            match="answer result not found",
    ):
        load_answer_result(
            tmp_path
            / "missing.json"
        )


def test_load_answer_result_invalid_json(
        tmp_path: Path,
) -> None:
    answer_path = (
            tmp_path
            / "bad.json"
    )

    answer_path.write_text(
        "{bad json",
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match=(
                    "invalid answer result JSON"
            ),
    ):
        load_answer_result(
            answer_path
        )
