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


class FakeRunner:
    def __init__(
        self,
    ) -> None:
        self.page = FakePage()

        self.calls: list[str] = []

        # 风控只触发一次
        self.risk_triggered = False

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

        # 第一次遇到“风控测试”时阻断
        if (
            question == "风控测试"
            and not self.risk_triggered
        ):
            self.risk_triggered = True

            raise QwenRiskControlError(
                "模拟千问真人验证"
            )

        return QwenAnswerResult(
            question=question,
            answer="测试回答",
            turn_id=(
                f"turn-{len(self.calls)}"
            ),
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


def test_batch_resume_after_risk_control(
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
            question="正常问题2",
            mode="quick",
        ),
    ]

    # =========================================
    # 第一次运行
    # =========================================

    first_results = batch.run(
        tasks
    )

    assert len(
        first_results
    ) == 2

    assert (
        first_results[0].status
        == "pass"
    )

    assert (
        first_results[1].status
        == "blocked"
    )

    # Q003 因为风控根本没有执行
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

    # =========================================
    # 检查第一次 summary
    # =========================================

    summary_path = (
        tmp_path
        / "batch_summary.json"
    )

    first_summary = json.loads(
        summary_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        first_summary["status"]
        == "blocked"
    )

    assert (
        first_summary["planned_count"]
        == 3
    )

    assert (
        first_summary["executed_count"]
        == 2
    )

    assert (
        first_summary["pass_count"]
        == 1
    )

    assert (
        first_summary["blocked_count"]
        == 1
    )

    assert (
        first_summary["pending_count"]
        == 1
    )

    # =========================================
    # 第二次断点续跑
    # =========================================

    second_results = batch.run(
        tasks,
        resume=True,
    )

    # =========================================
    # Q001 不应该再次调用
    # =========================================

    assert runner.calls == [
        "正常问题1",
        "风控测试",
        "风控测试",
        "正常问题2",
    ]

    # Q001 只出现一次，
    # 证明第二次被真正 SKIP
    assert (
        runner.calls.count(
            "正常问题1"
        )
        == 1
    )

    # =========================================
    # 最终结果全部 PASS
    # =========================================

    assert len(
        second_results
    ) == 3

    assert all(
        item.status == "pass"
        for item in second_results
    )

    # =========================================
    # 文件状态
    # =========================================

    assert (
        tmp_path
        / "Q001_quick.json"
    ).exists()

    assert (
        tmp_path
        / "Q002_quick.json"
    ).exists()

    assert (
        tmp_path
        / "Q003_quick.json"
    ).exists()

    # 重跑成功以后，
    # 旧 blocked 文件必须被清掉
    assert not (
        tmp_path
        / "Q002_quick_blocked.json"
    ).exists()

    # =========================================
    # 最终 summary
    # =========================================

    final_summary = json.loads(
        summary_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        final_summary["status"]
        == "completed"
    )

    assert (
        final_summary["planned_count"]
        == 3
    )

    assert (
        final_summary["executed_count"]
        == 3
    )

    assert (
        final_summary["pass_count"]
        == 3
    )

    assert (
        final_summary["fail_count"]
        == 0
    )

    assert (
        final_summary["blocked_count"]
        == 0
    )

    assert (
        final_summary["pending_count"]
        == 0
    )

    assert (
        len(
            final_summary["task_results"]
        )
        == 3
    )