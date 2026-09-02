from __future__ import annotations

import json
from pathlib import Path

from app.qwen.package.assembly import (
    assemble_central_package_records,
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


def test_assemble_central_package_records(
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
            "2026-09-01T12:00:00"
        ),
        "finished_at": (
            "2026-09-01T12:05:00"
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
            "关键词1"
        ],
        "sources": [
            {
                "rank": 1,
                "title": "来源一",
                "url": (
                    "https://example.com/1"
                ),
            }
        ],
        "citation_mapping_available": False,
        "acquired_at": (
            "2026-09-01T12:02:00"
        ),
    }

    write_json(
        tmp_path
        / "Q001_research.json",
        answer,
    )

    records = (
        assemble_central_package_records(
            tmp_path,
            batch_id="batch-001",
        )
    )

    assert len(records.tasks) == 2
    assert len(records.answers) == 1
    assert len(records.sources) == 1

    assert (
        records.tasks[0].mode_code
        == "expert"
    )

    assert (
        records.tasks[0].task_status
        == "success"
    )

    assert (
        records.tasks[1].task_status
        == "failed"
    )

    answer_record = (
        records.answers[0]
    )

    assert (
        answer_record.mode_code
        == "expert"
    )

    assert (
        answer_record.question_text
        == "研究问题"
    )

    assert (
        answer_record.answer_text_clean
        == "研究回答"
    )

    assert (
        answer_record.task_id
        == records.tasks[0].task_id
    )

    assert (
        records.sources[0].answer_id
        == answer_record.answer_id
    )

    assert (
        records.sources[0].source_order
        == 1
    )

    assert (
        records.sources[0].source_url_raw
        == "https://example.com/1"
    )
