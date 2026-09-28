from __future__ import annotations

import json
from pathlib import Path

from app.qwen.models import (
    QwenAnswerResult,
)
from app.qwen.serialization import (
    write_result_json,
)


def test_qwen_answer_result_serializes_screenshot_metadata(
    tmp_path: Path,
) -> None:
    result = QwenAnswerResult(
        question="鸿茅药酒是药还是酒？",
        answer="测试回答",
        turn_id="turn-001",
        chat_url="https://www.qianwen.com/chat/test",
        mode="quick",
        mode_label="快速",
        question_id="Q001",
        screenshot_path=(
            "screenshots/Q001_quick.png"
        ),
        screenshot_sha256="abc123",
        screenshot_size_bytes=123456,
        screenshot_width=1920,
        screenshot_height=4320,
    )

    output_path = (
        tmp_path
        / "Q001_quick.json"
    )

    write_result_json(
        result,
        output_path,
    )

    data = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert data["screenshot_path"] == (
        "screenshots/Q001_quick.png"
    )
    assert data["screenshot_sha256"] == "abc123"
    assert data["screenshot_size_bytes"] == 123456
    assert data["screenshot_width"] == 1920
    assert data["screenshot_height"] == 4320


def test_qwen_answer_result_screenshot_metadata_defaults_to_none() -> None:
    result = QwenAnswerResult(
        question="测试问题",
        answer="测试回答",
        turn_id="turn-002",
        chat_url="https://www.qianwen.com/chat/test",
    )

    assert result.screenshot_path is None
    assert result.screenshot_sha256 is None
    assert result.screenshot_size_bytes is None
    assert result.screenshot_width is None
    assert result.screenshot_height is None