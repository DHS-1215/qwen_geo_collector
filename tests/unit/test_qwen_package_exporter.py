from __future__ import annotations

import json
from pathlib import Path

from app.qwen.package.exporter import (
    export_package_directory,
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


def test_export_package_directory(
        tmp_path: Path,
) -> None:
    batch_dir = (
            tmp_path
            / "batch"
    )

    output_dir = (
            tmp_path
            / "package"
    )

    batch_dir.mkdir()

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
        batch_dir
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
        batch_dir
        / "Q001_research.json",
        answer,
    )

    result_dir = (
        export_package_directory(
            batch_dir=batch_dir,
            output_dir=output_dir,
            package_id=(
                "qwen-test-package"
            ),
        )
    )

    assert (
            result_dir
            == output_dir
    )

    # =========================================
    # 文件必须全部生成
    # =========================================

    manifest_path = (
            output_dir
            / "manifest.json"
    )

    tasks_path = (
            output_dir
            / "tasks.jsonl"
    )

    answers_path = (
            output_dir
            / "answers.jsonl"
    )

    sources_path = (
            output_dir
            / "sources.jsonl"
    )

    checksums_path = (
            output_dir
            / "checksums.json"
    )

    assert manifest_path.exists()
    assert tasks_path.exists()
    assert answers_path.exists()
    assert sources_path.exists()
    assert checksums_path.exists()

    # =========================================
    # manifest
    # =========================================

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
            manifest["schema_version"]
            == "geo_batch_v1"
    )

    assert (
            manifest["platform"]
            == "qwen"
    )

    assert (
            manifest["package_id"]
            == "qwen-test-package"
    )

    assert (
            manifest["task_count"]
            == 2
    )

    assert (
            manifest["answer_count"]
            == 1
    )

    assert (
            manifest["source_count"]
            == 2
    )

    assert (
            manifest["files"]
            == [
                "manifest.json",
                "tasks.jsonl",
                "answers.jsonl",
                "sources.jsonl",
                "checksums.json",
            ]
    )

    # =========================================
    # tasks
    # =========================================

    task_lines = (
        tasks_path
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    )

    assert len(
        task_lines
    ) == 2

    tasks = [
        json.loads(line)
        for line in task_lines
    ]

    assert (
            tasks[0]["status"]
            == "pass"
    )

    assert (
            tasks[1]["status"]
            == "fail"
    )

    checksums = json.loads(
        checksums_path.read_text(
            encoding="utf-8"
        )
    )

    assert set(
        checksums
    ) == {
               "manifest.json",
               "tasks.jsonl",
               "answers.jsonl",
               "sources.jsonl",
           }

    for checksum in checksums.values():
        assert len(checksum) == 64

    # =========================================
    # answers
    # =========================================

    answer_lines = (
        answers_path
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    )

    assert len(
        answer_lines
    ) == 1

    exported_answer = json.loads(
        answer_lines[0]
    )

    assert (
            exported_answer[
                "question_id"
            ]
            == "Q001"
    )

    assert (
            exported_answer[
                "mode"
            ]
            == "research"
    )

    # =========================================
    # sources
    # =========================================

    source_lines = (
        sources_path
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    )

    assert len(
        source_lines
    ) == 2

    sources = [
        json.loads(line)
        for line in source_lines
    ]

    assert (
            sources[0]["rank"]
            == 1
    )

    assert (
            sources[1]["rank"]
            == 2
    )

    assert (
            sources[0]["occurrence_id"]
            != sources[1]["occurrence_id"]
    )
