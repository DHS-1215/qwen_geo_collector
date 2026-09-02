from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qwen.package.assembly import (
    assemble_package_records,
)


def write_json(
        path: Path,
        data: dict,
) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_assemble_package_records(
        tmp_path: Path,
) -> None:
    summary = {
        "platform": "qwen",
        "status": "partial",
        "planned_count": 2,
        "executed_count": 2,
        "pass_count": 1,
        "fail_count": 1,
        "blocked_count": 0,
        "pending_count": 0,
        "task_results": [
            {
                "question_id": "Q001",
                "mode": "research",
                "question": "研究问题",
                "status": "pass",
                "output_path": (
                    "Q001_research.json"
                ),
                "error_type": None,
                "error_message": None,
            },
            {
                "question_id": "Q002",
                "mode": "quick",
                "question": "失败问题",
                "status": "fail",
                "output_path": None,
                "error_type": "RuntimeError",
                "error_message": "模拟失败",
            },
        ],
        "started_at": (
            "2026-08-28T13:00:00"
        ),
        "finished_at": (
            "2026-08-28T13:05:00"
        ),
    }

    write_json(
        tmp_path
        / "batch_summary.json",
        summary,
    )

    answer = {
        "platform": "qwen",
        "question_id": "Q001",
        "question": "研究问题",
        "answer": "研究回答",
        "turn_id": "turn-001",
        "chat_url": (
            "https://www.qianwen.com/"
            "chat/test"
        ),
        "mode": "research",
        "mode_label": "思考研究",
        "search_queries": [
            "关键词1",
            "关键词2",
        ],
        "sources": [
            {
                "rank": 1,
                "title": "来源一",
                "url": (
                    "https://example.com/1"
                ),
            },
            {
                "rank": 2,
                "title": "来源二",
                "url": (
                    "https://example.com/2"
                ),
            },
        ],
        "citation_mapping_available": False,
        "acquired_at": (
            "2026-08-28T13:02:00"
        ),
    }

    write_json(
        tmp_path
        / "Q001_research.json",
        answer,
    )

    records = assemble_package_records(
        tmp_path
    )

    assert len(
        records.tasks
    ) == 2

    assert len(
        records.answers
    ) == 1

    assert len(
        records.sources
    ) == 2

    assert (
            records.tasks[0].status
            == "pass"
    )

    assert (
            records.tasks[1].status
            == "fail"
    )

    assert (
            records.answers[0].question_id
            == "Q001"
    )

    assert (
            records.sources[0].rank
            == 1
    )

    assert (
            records.sources[1].rank
            == 2
    )


def test_pending_batch_is_rejected(
        tmp_path: Path,
) -> None:
    summary = {
        "platform": "qwen",
        "status": "blocked",
        "planned_count": 3,
        "executed_count": 2,
        "pass_count": 1,
        "fail_count": 0,
        "blocked_count": 1,
        "pending_count": 1,
        "task_results": [
            {
                "question_id": "Q001",
                "mode": "quick",
                "question": "正常问题",
                "status": "pass",
                "output_path": (
                    "Q001_quick.json"
                ),
                "error_type": None,
                "error_message": None,
            },
            {
                "question_id": "Q002",
                "mode": "quick",
                "question": "风控问题",
                "status": "blocked",
                "output_path": None,
                "error_type": (
                    "QwenRiskControlError"
                ),
                "error_message": (
                    "模拟真人验证"
                ),
            },
        ],
        "started_at": (
            "2026-08-28T13:00:00"
        ),
        "finished_at": (
            "2026-08-28T13:01:00"
        ),
    }

    write_json(
        tmp_path
        / "batch_summary.json",
        summary,
    )

    with pytest.raises(
            ValueError,
            match="pending tasks",
    ):
        assemble_package_records(
            tmp_path
        )


def test_answer_question_id_mismatch_is_rejected(
        tmp_path: Path,
) -> None:
    summary = {
        "platform": "qwen",
        "status": "completed",
        "planned_count": 1,
        "executed_count": 1,
        "pass_count": 1,
        "fail_count": 0,
        "blocked_count": 0,
        "pending_count": 0,
        "task_results": [
            {
                "question_id": "Q001",
                "mode": "quick",
                "question": "测试问题",
                "status": "pass",
                "output_path": (
                    "Q001_quick.json"
                ),
                "error_type": None,
                "error_message": None,
            }
        ],
        "started_at": (
            "2026-08-28T13:00:00"
        ),
        "finished_at": (
            "2026-08-28T13:01:00"
        ),
    }

    write_json(
        tmp_path
        / "batch_summary.json",
        summary,
    )

    answer = {
        "platform": "qwen",
        "question_id": "Q999",
        "question": "测试问题",
        "answer": "测试回答",
        "turn_id": "turn-001",
        "chat_url": (
            "https://www.qianwen.com/"
            "chat/test"
        ),
        "mode": "quick",
        "mode_label": "快速",
        "search_queries": [],
        "sources": [],
        "citation_mapping_available": False,
        "acquired_at": (
            "2026-08-28T13:00:30"
        ),
    }

    write_json(
        tmp_path
        / "Q001_quick.json",
        answer,
    )

    with pytest.raises(
            ValueError,
            match="question_id mismatch",
    ):
        assemble_package_records(
            tmp_path
        )


def test_answer_mode_mismatch_is_rejected(
        tmp_path: Path,
) -> None:
    summary = {
        "platform": "qwen",
        "status": "completed",
        "planned_count": 1,
        "executed_count": 1,
        "pass_count": 1,
        "fail_count": 0,
        "blocked_count": 0,
        "pending_count": 0,
        "task_results": [
            {
                "question_id": "Q001",
                "mode": "quick",
                "question": "测试问题",
                "status": "pass",
                "output_path": (
                    "Q001_quick.json"
                ),
                "error_type": None,
                "error_message": None,
            }
        ],
        "started_at": (
            "2026-08-28T13:00:00"
        ),
        "finished_at": (
            "2026-08-28T13:01:00"
        ),
    }

    write_json(
        tmp_path
        / "batch_summary.json",
        summary,
    )

    answer = {
        "platform": "qwen",
        "question_id": "Q001",
        "question": "测试问题",
        "answer": "测试回答",
        "turn_id": "turn-001",
        "chat_url": (
            "https://www.qianwen.com/"
            "chat/test"
        ),
        "mode": "research",
        "mode_label": "思考研究",
        "search_queries": [],
        "sources": [],
        "citation_mapping_available": False,
        "acquired_at": (
            "2026-08-28T13:00:30"
        ),
    }

    write_json(
        tmp_path
        / "Q001_quick.json",
        answer,
    )

    with pytest.raises(
            ValueError,
            match="mode mismatch",
    ):
        assemble_package_records(
            tmp_path
        )
