from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

from app.qwen.batch import (
    QwenBatchRunner,
)
from app.qwen.models import (
    QwenAnswerResult,
)
from app.qwen.tasks import (
    QwenTask,
)


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunk(
    chunk_type: bytes,
    data: bytes,
) -> bytes:
    crc = zlib.crc32(
        chunk_type
    )
    crc = zlib.crc32(
        data,
        crc,
    ) & 0xFFFFFFFF

    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", crc)
    )


def _make_png(
    width: int = 640,
    height: int = 480,
) -> bytes:
    ihdr = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,
        2,
        0,
        0,
        0,
    )

    scanline = (
        b"\x00"
        + b"\x00\x00\x00" * width
    )

    raw_image = (
        scanline * height
    )

    return (
        PNG_SIGNATURE
        + _png_chunk(
            b"IHDR",
            ihdr,
        )
        + _png_chunk(
            b"IDAT",
            zlib.compress(raw_image),
        )
        + _png_chunk(
            b"IEND",
            b"",
        )
    )


class FakePage:
    def __init__(self) -> None:
        self.calls: list[
            tuple[str, bool]
        ] = []

    def screenshot(
        self,
        *,
        path: str,
        full_page: bool,
    ) -> bytes:
        self.calls.append(
            (
                path,
                full_page,
            )
        )

        payload = _make_png(
            1280,
            3000,
        )

        Path(path).write_bytes(
            payload
        )

        return payload


class FakeRunner:
    def __init__(self) -> None:
        self.page = FakePage()

    def ask(
        self,
        question: str,
        *,
        mode: str,
        new_chat: bool,
        answer_timeout_seconds: int,
    ) -> QwenAnswerResult:
        return QwenAnswerResult(
            question=question,
            answer="测试回答",
            turn_id="turn-001",
            chat_url=(
                "https://www.qianwen.com/chat/test"
            ),
            mode=mode,
            mode_label=(
                "快速"
                if mode == "quick"
                else "思考研究"
            ),
        )


def test_run_task_captures_screenshot_and_writes_metadata(
    tmp_path: Path,
) -> None:
    runner = FakeRunner()

    batch = QwenBatchRunner(
        runner=runner,
        output_dir=tmp_path,
    )

    task = QwenTask(
        question_id="Q001",
        question="测试问题",
        mode="quick",
    )

    result = batch.run_task(
        task
    )

    screenshot_path = (
        tmp_path
        / "screenshots"
        / "Q001_quick.png"
    )

    assert screenshot_path.exists()

    assert runner.page.calls == [
        (
            str(screenshot_path),
            True,
        )
    ]

    assert result.screenshot_path == (
        "screenshots/Q001_quick.png"
    )
    assert result.screenshot_sha256
    assert result.screenshot_size_bytes
    assert result.screenshot_size_bytes > 0
    assert result.screenshot_width == 1280
    assert result.screenshot_height == 3000

    answer_path = (
        tmp_path
        / "Q001_quick.json"
    )

    assert answer_path.exists()

    data = json.loads(
        answer_path.read_text(
            encoding="utf-8"
        )
    )

    assert data["screenshot_path"] == (
        "screenshots/Q001_quick.png"
    )
    assert data["screenshot_sha256"] == (
        result.screenshot_sha256
    )
    assert data["screenshot_width"] == 1280
    assert data["screenshot_height"] == 3000