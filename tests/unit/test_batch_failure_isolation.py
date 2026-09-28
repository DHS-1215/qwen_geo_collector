from __future__ import annotations

import json
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
        payload = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de0000000c49444154789c63606060000000040001f61738550000000049454e44ae426082")

        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        Path(path).write_bytes(
            payload
        )

        return payload


class FakeRunner:
    def __init__(
        self,
    ) -> None:
        self.page = FakePage()

    def ask(
        self,
        question: str,
        *,
        mode: str,
        new_chat: bool,
        answer_timeout_seconds: int,
    ) -> QwenAnswerResult:
        if "失败测试" in question:
            raise RuntimeError(
                "模拟采集失败"
            )

        return QwenAnswerResult(
            question=question,
            answer="测试回答",
            turn_id="test-turn",
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


def test_batch_continues_after_failure(
    tmp_path: Path,
) -> None:
    runner = FakeRunner()

    batch = QwenBatchRunner(
        runner=runner,
        output_dir=tmp_path,
    )

    tasks = [
        QwenTask(
            question_id="Q001",
            question="正常问题1",
            mode="quick",
        ),
        QwenTask(
            question_id="Q002",
            question="失败测试",
            mode="quick",
        ),
        QwenTask(
            question_id="Q003",
            question="正常问题2",
            mode="quick",
        ),
    ]

    results = batch.run(
        tasks
    )

    assert len(results) == 3

    assert (
        results[0].status
        == "pass"
    )

    assert (
        results[1].status
        == "fail"
    )

    assert (
        results[2].status
        == "pass"
    )

    assert (
        results[1].error_type
        == "RuntimeError"
    )

    assert (
        "模拟采集失败"
        in results[1].error_message
    )

    assert (
        tmp_path
        / "Q001_quick.json"
    ).exists()

    assert (
        tmp_path
        / "Q002_quick_failed.json"
    ).exists()

    assert (
        tmp_path
        / "Q003_quick.json"
    ).exists()

    # =========================================
    # batch_summary.json
    # =========================================

    summary_path = (
        tmp_path
        / "batch_summary.json"
    )

    assert summary_path.exists()

    summary = json.loads(
        summary_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        summary["status"]
        == "partial"
    )

    assert (
        summary["planned_count"]
        == 3
    )

    assert (
        summary["executed_count"]
        == 3
    )

    assert (
        summary["pass_count"]
        == 2
    )

    assert (
        summary["fail_count"]
        == 1
    )

    assert (
        summary["blocked_count"]
        == 0
    )

    assert (
        summary["pending_count"]
        == 0
    )

    assert (
        len(
            summary["task_results"]
        )
        == 3
    )
