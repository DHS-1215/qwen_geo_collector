from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qwen.batch import (
    QwenBatchRunner,
)
from app.qwen.models import (
    QwenAnswerResult,
)
from app.qwen.screenshot import (
    validate_qwen_screenshot,
)
from app.qwen.tasks import (
    QwenTask,
)


PNG_HEX = (
    "89504e470d0a1a0a"
    "0000000d49484452"
    "0000000100000001"
    "0802000000907753de"
    "0000000c49444154"
    "789c63606060000000040001f6173855"
    "0000000049454e44ae426082"
)


class FakePage:
    def wait_for_timeout(
        self,
        milliseconds: int,
    ) -> None:
        pass

    def screenshot(
        self,
        *,
        path: str,
        full_page: bool,
    ) -> bytes:
        payload = bytes.fromhex(
            PNG_HEX
        )

        output_path = Path(path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_bytes(
            payload
        )

        return payload


class FakeRunner:
    def __init__(self) -> None:
        self.page = FakePage()
        self.calls: list[str] = []

    def ask(
        self,
        question: str,
        *,
        mode: str,
        new_chat: bool,
        answer_timeout_seconds: int,
    ) -> QwenAnswerResult:
        self.calls.append(
            question
        )

        return QwenAnswerResult(
            question=question,
            answer="重新采集后的回答",
            turn_id="turn-new",
            chat_url=(
                "https://www.qianwen.com/chat/test"
            ),
            mode=mode,
            mode_label="快速",
        )


def _prepare_passed_task(
    tmp_path: Path,
    runner: FakeRunner,
) -> tuple[
    QwenTask,
    Path,
    dict,
]:
    task = QwenTask(
        question_id="Q100",
        question="截图断点校验",
        mode="quick",
    )

    (
        tmp_path
        / "batch_summary.json"
    ).write_text(
        json.dumps(
            {
                "task_results": [
                    {
                        "question_id": (
                            task.question_id
                        ),
                        "mode": task.mode,
                        "question": task.question,
                        "status": "pass",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    screenshot_path = (
        tmp_path
        / "screenshots"
        / "Q100_quick.png"
    )

    runner.page.screenshot(
        path=str(screenshot_path),
        full_page=True,
    )

    screenshot = (
        validate_qwen_screenshot(
            screenshot_path
        )
    )

    answer_data = {
        "question_id": task.question_id,
        "mode": task.mode,
        "answer": "已有回答",
        "screenshot_path": (
            "screenshots/Q100_quick.png"
        ),
        "screenshot_sha256": (
            screenshot.sha256
        ),
        "screenshot_size_bytes": (
            screenshot.size_bytes
        ),
        "screenshot_width": (
            screenshot.width
        ),
        "screenshot_height": (
            screenshot.height
        ),
    }

    answer_path = (
        tmp_path
        / "Q100_quick.json"
    )

    answer_path.write_text(
        json.dumps(
            answer_data
        ),
        encoding="utf-8",
    )

    return (
        task,
        screenshot_path,
        answer_data,
    )


@pytest.mark.parametrize(
    "case",
    [
        "missing_path",
        "wrong_path",
        "missing_file",
        "corrupt_png",
        "sha_mismatch",
        "size_mismatch",
        "width_mismatch",
        "height_mismatch",
    ],
)
def test_resume_retries_when_screenshot_evidence_invalid(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    runner = FakeRunner()

    batch = QwenBatchRunner(
        runner=runner,
        output_dir=tmp_path,
    )

    (
        task,
        screenshot_path,
        answer_data,
    ) = _prepare_passed_task(
        tmp_path,
        runner,
    )

    answer_path = (
        tmp_path
        / "Q100_quick.json"
    )

    if case == "missing_path":
        answer_data.pop(
            "screenshot_path"
        )

    elif case == "wrong_path":
        answer_data[
            "screenshot_path"
        ] = "../Q100_quick.png"

    elif case == "missing_file":
        screenshot_path.unlink()

    elif case == "corrupt_png":
        screenshot_path.write_bytes(
            b"not-a-valid-png"
        )

    elif case == "sha_mismatch":
        answer_data[
            "screenshot_sha256"
        ] = "bad-sha256"

    elif case == "size_mismatch":
        answer_data[
            "screenshot_size_bytes"
        ] += 1

    elif case == "width_mismatch":
        answer_data[
            "screenshot_width"
        ] += 1

    elif case == "height_mismatch":
        answer_data[
            "screenshot_height"
        ] += 1

    answer_path.write_text(
        json.dumps(
            answer_data
        ),
        encoding="utf-8",
    )

    results = batch.run(
        [task],
        resume=True,
    )

    assert len(results) == 1
    assert results[0].status == "pass"

    assert runner.calls == [
        task.question
    ]

    output = (
        capsys.readouterr().out
    )

    assert (
        "[RESUME INVALID PASS]"
        in output
    )

    repaired = json.loads(
        answer_path.read_text(
            encoding="utf-8"
        )
    )

    assert repaired[
        "screenshot_path"
    ] == (
        "screenshots/Q100_quick.png"
    )


def test_resume_skips_when_screenshot_evidence_is_valid(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = FakeRunner()

    batch = QwenBatchRunner(
        runner=runner,
        output_dir=tmp_path,
    )

    (
        task,
        _,
        _,
    ) = _prepare_passed_task(
        tmp_path,
        runner,
    )

    results = batch.run(
        [task],
        resume=True,
    )

    assert len(results) == 1
    assert results[0].status == "pass"

    assert runner.calls == []

    output = (
        capsys.readouterr().out
    )

    assert "[TASK SKIP]" in output