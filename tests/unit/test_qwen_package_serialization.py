from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.qwen.package.models import (
    QwenPackageManifest,
    QwenPackageTask,
)
from app.qwen.package.serialization import (
    model_to_dict,
    write_json,
    write_jsonl,
)


def test_model_to_dict_serializes_datetime() -> None:
    manifest = QwenPackageManifest(
        package_id="qwen-test-001",
        created_at=datetime(
            2026,
            8,
            28,
            12,
            0,
        ),
        task_count=1,
        answer_count=1,
        source_count=0,
    )

    data = model_to_dict(
        manifest
    )

    assert (
            data["package_id"]
            == "qwen-test-001"
    )

    assert (
            data["created_at"]
            == "2026-08-28T12:00:00"
    )


def test_write_json_preserves_chinese(
        tmp_path: Path,
) -> None:
    manifest = QwenPackageManifest(
        package_id="千问测试包",
        created_at=datetime(
            2026,
            8,
            28,
            12,
            5,
        ),
        task_count=1,
        answer_count=1,
        source_count=0,
        files=[
            "tasks.jsonl",
        ],
    )

    output_path = (
            tmp_path
            / "manifest.json"
    )

    result_path = write_json(
        manifest,
        output_path,
    )

    assert (
            result_path
            == output_path
    )

    assert output_path.exists()

    content = output_path.read_text(
        encoding="utf-8"
    )

    assert "千问测试包" in content

    assert "\\u5343" not in content

    data = json.loads(
        content
    )

    assert (
            data["platform"]
            == "qwen"
    )


def test_write_jsonl_one_object_per_line(
        tmp_path: Path,
) -> None:
    tasks = [
        QwenPackageTask(
            question_id="Q001",
            question="第一个问题",
            mode="quick",
            status="pass",
        ),
        QwenPackageTask(
            question_id="Q002",
            question="第二个问题",
            mode="research",
            status="blocked",
            error_type=(
                "QwenRiskControlError"
            ),
            error_message=(
                "模拟真人验证"
            ),
        ),
    ]

    output_path = (
            tmp_path
            / "tasks.jsonl"
    )

    write_jsonl(
        tasks,
        output_path,
    )

    content = output_path.read_text(
        encoding="utf-8"
    )

    lines = content.splitlines()

    assert len(lines) == 2

    first = json.loads(
        lines[0]
    )

    second = json.loads(
        lines[1]
    )

    assert (
            first["question_id"]
            == "Q001"
    )

    assert (
            first["question"]
            == "第一个问题"
    )

    assert (
            second["question_id"]
            == "Q002"
    )

    assert (
            second["status"]
            == "blocked"
    )

    assert (
            second["error_type"]
            == "QwenRiskControlError"
    )


def test_write_jsonl_empty_list(
        tmp_path: Path,
) -> None:
    output_path = (
            tmp_path
            / "empty.jsonl"
    )

    write_jsonl(
        [],
        output_path,
    )

    assert output_path.exists()

    assert (
            output_path.read_text(
                encoding="utf-8"
            )
            == ""
    )
