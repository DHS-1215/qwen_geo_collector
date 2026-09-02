from __future__ import annotations

import json
from pathlib import Path

from app.qwen.package.exporter import (
    export_central_package_directory,
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


def test_export_central_package_directory(
    tmp_path: Path,
) -> None:
    batch_dir = (
        tmp_path
        / "batch"
    )

    package_dir = (
        tmp_path
        / "package"
    )

    batch_dir.mkdir()

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
                "mode": "research",
                "question": "研究问题",
                "status": "pass",
                "output_path": (
                    "Q001_research.json"
                ),
                "error_type": None,
                "error_message": None,
            }
        ],
        "started_at": (
            "2026-09-01T12:00:00"
        ),
        "finished_at": (
            "2026-09-01T12:05:00"
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
        "search_queries": [],
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
        batch_dir
        / "Q001_research.json",
        answer,
    )

    export_central_package_directory(
        batch_dir=batch_dir,
        output_dir=package_dir,
        batch_id="qwen-central-test",
        product_id="hongmao",
        product_name="鸿茅药酒",
    )

    manifest = json.loads(
        (
            package_dir
            / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest["schema_version"]
        == "geo_package_v1"
    )

    assert (
        manifest["geo_batch_version"]
        == "geo_batch_v1"
    )

    assert (
        manifest["platform_code"]
        == "qwen"
    )

    assert (
        manifest["platform_name"]
        == "千问"
    )

    assert (
        manifest["product_id"]
        == "hongmao"
    )

    assert (
        manifest["product_name"]
        == "鸿茅药酒"
    )

    assert (
        manifest["batch_id"]
        == "qwen-central-test"
    )

    task = json.loads(
        (
            package_dir
            / "tasks.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()[0]
    )

    assert task["mode_code"] == "expert"
    assert task["task_status"] == "success"
    assert task["task_id"]

    answer_record = json.loads(
        (
            package_dir
            / "answers.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()[0]
    )

    assert (
        answer_record["task_id"]
        == task["task_id"]
    )

    assert (
        answer_record["answer_text_raw"]
        == "研究回答"
    )

    assert (
        answer_record["mode_code"]
        == "expert"
    )

    assert (
        answer_record[
            "platform_meta_json"
        ]["original_mode"]
        == "research"
    )

    source = json.loads(
        (
            package_dir
            / "sources.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()[0]
    )

    assert (
        source["answer_id"]
        == answer_record["answer_id"]
    )

    assert (
        source["source_order"]
        == 1
    )

    assert (
        source["source_url_raw"]
        == "https://example.com/1"
    )
