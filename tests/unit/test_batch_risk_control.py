from __future__ import annotations

import json
from pathlib import Path

from app.qwen.batch import (
    QwenBatchRunner,
)
from app.qwen.exceptions import (
    QwenRiskControlError,
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

        if question == "风控测试":
            raise QwenRiskControlError(
                "模拟千问真人验证"
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


def test_batch_stops_on_risk_control(
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
            question="风控测试",
            mode="quick",
        ),
        QwenTask(
            question_id="Q003",
            question="绝对不应该执行",
            mode="quick",
        ),
    ]

    results = batch.run(
        tasks
    )

    # 只执行到 Q002
    assert len(results) == 2

    assert (
        results[0].status
        == "pass"
    )

    assert (
        results[1].status
        == "blocked"
    )

    # Q003 根本没有请求
    assert runner.calls == [
        "正常问题1",
        "风控测试",
    ]

    assert (
        tmp_path
        / "Q001_quick.json"
    ).exists()

    assert (
        tmp_path
        / "Q002_quick_blocked.json"
    ).exists()

    assert not (
        tmp_path
        / "Q003_quick.json"
    ).exists()

    assert (
        results[1].error_type
        == "QwenRiskControlError"
    )

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
        == "blocked"
    )

    assert (
        summary["planned_count"]
        == 3
    )

    assert (
        summary["executed_count"]
        == 2
    )

    assert (
        summary["pass_count"]
        == 1
    )

    assert (
        summary["fail_count"]
        == 0
    )

    assert (
        summary["blocked_count"]
        == 1
    )

    assert (
        summary["pending_count"]
        == 1
    )

    assert (
        len(
            summary["task_results"]
        )
        == 2
    )
