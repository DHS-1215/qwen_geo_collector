from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.runner import (
    load_analysis_items,
    run_mention_analysis,
)


def write_json(
    path: Path,
    data: dict,
) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def make_answer_data(
    question_id: str,
    mode: str,
    answer: str,
) -> dict:
    return {
        "platform": "qwen",
        "question": "测试问题",
        "answer": answer,
        "turn_id": f"{question_id}-{mode}",
        "chat_url": (
            "https://www.qianwen.com/chat/test"
        ),
        "mode": mode,
        "mode_label": (
            "快速"
            if mode == "quick"
            else "思考研究"
        ),
        "question_id": question_id,
        "search_queries": [],
        "sources": [],
        "citation_mapping_available": False,
        "acquired_at": (
            datetime.now().isoformat()
        ),
    }


def write_batch_summary(
    batch_dir: Path,
    task_results: list[dict],
) -> None:
    pass_count = sum(
        1
        for item in task_results
        if item["status"] == "pass"
    )

    fail_count = sum(
        1
        for item in task_results
        if item["status"] == "fail"
    )

    blocked_count = sum(
        1
        for item in task_results
        if item["status"] == "blocked"
    )

    now = datetime.now().isoformat()

    write_json(
        batch_dir / "batch_summary.json",
        {
            "platform": "qwen",
            "status": "completed",
            "planned_count": len(
                task_results
            ),
            "executed_count": len(
                task_results
            ),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "blocked_count": blocked_count,
            "pending_count": 0,
            "task_results": task_results,
            "started_at": now,
            "finished_at": now,
        },
    )


def test_load_analysis_items_loads_only_pass_answers(
    tmp_path: Path,
) -> None:
    answer_path = (
        tmp_path
        / "Q001_quick.json"
    )

    write_json(
        answer_path,
        make_answer_data(
            "Q001",
            "quick",
            "鸿茅药酒被提及。",
        ),
    )

    write_batch_summary(
        tmp_path,
        [
            {
                "question_id": "Q001",
                "mode": "quick",
                "question": "测试问题",
                "status": "pass",
                "output_path": str(
                    answer_path
                ),
            },
            {
                "question_id": "Q002",
                "mode": "research",
                "question": "测试问题",
                "status": "fail",
                "output_path": (
                    "does-not-need-to-exist.json"
                ),
            },
        ],
    )

    items = load_analysis_items(
        tmp_path
    )

    assert len(items) == 2

    assert items[0][1] is not None
    assert (
        items[0][1].answer
        == "鸿茅药酒被提及。"
    )

    assert items[1][1] is None


def test_run_mention_analysis_from_batch(
    tmp_path: Path,
) -> None:
    quick_path = (
        tmp_path
        / "Q001_quick.json"
    )
    research_path = (
        tmp_path
        / "Q001_research.json"
    )

    write_json(
        quick_path,
        make_answer_data(
            "Q001",
            "quick",
            "没有提及目标产品。",
        ),
    )

    write_json(
        research_path,
        make_answer_data(
            "Q001",
            "research",
            "鸿 茅 药 酒被提及。",
        ),
    )

    write_batch_summary(
        tmp_path,
        [
            {
                "question_id": "Q001",
                "mode": "quick",
                "question": "测试问题",
                "status": "pass",
                "output_path": str(
                    quick_path
                ),
            },
            {
                "question_id": "Q001",
                "mode": "research",
                "question": "测试问题",
                "status": "pass",
                "output_path": str(
                    research_path
                ),
            },
        ],
    )

    result = run_mention_analysis(
        tmp_path,
        [
            MentionTarget(
                target_id="hongmao",
                aliases=["鸿茅药酒"],
            )
        ],
    )

    summary = result.summaries[
        "hongmao"
    ]

    assert summary.quick.valid_count == 1
    assert (
        summary.quick.mentioned_count
        == 0
    )

    assert (
        summary.research.valid_count
        == 1
    )
    assert (
        summary.research.mentioned_count
        == 1
    )

    assert (
        summary.all_answers.valid_count
        == 2
    )
    assert (
        summary.all_answers.mention_rate
        == 0.5
    )

    assert (
        summary.question_level.valid_count
        == 1
    )
    assert (
        summary.question_level.mention_rate
        == 1.0
    )


def test_pass_task_without_output_path_fails(
    tmp_path: Path,
) -> None:
    write_batch_summary(
        tmp_path,
        [
            {
                "question_id": "Q001",
                "mode": "quick",
                "question": "测试问题",
                "status": "pass",
                "output_path": None,
            }
        ],
    )

    with pytest.raises(
        ValueError,
        match=(
            "pass task missing output_path"
        ),
    ):
        load_analysis_items(
            tmp_path
        )


def test_missing_pass_answer_file_fails(
    tmp_path: Path,
) -> None:
    write_batch_summary(
        tmp_path,
        [
            {
                "question_id": "Q001",
                "mode": "quick",
                "question": "测试问题",
                "status": "pass",
                "output_path": (
                    "Q001_quick.json"
                ),
            }
        ],
    )

    with pytest.raises(
        FileNotFoundError,
        match="answer result not found",
    ):
        load_analysis_items(
            tmp_path
        )
