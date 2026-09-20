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


QUOTA_TEXT = (
    "今日使用次数已达上限"
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
        quota_remaining: dict[str, int] | None = None,
    ) -> None:
        self.page = FakePage()
        self.calls: list[str] = []
        self.quota_remaining = dict(
            quota_remaining or {}
        )

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

        remaining = (
            self.quota_remaining.get(
                question,
                0,
            )
        )

        if remaining > 0:
            self.quota_remaining[
                question
            ] = remaining - 1

            answer = QUOTA_TEXT

        else:
            answer = (
                f"正常回答：{question}"
            )

        return QwenAnswerResult(
            question=question,
            answer=answer,
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


def build_tasks() -> list[QwenTask]:
    return [
        QwenTask(
            question_id="Q001",
            question="已经完成的问题",
            mode="quick",
        ),
        QwenTask(
            question_id="Q002",
            question="额度不足的问题",
            mode="research",
        ),
        QwenTask(
            question_id="Q003",
            question="额度后面的任务",
            mode="quick",
        ),
    ]


def test_quota_pause_then_resume_from_current_task(
    tmp_path: Path,
    capsys,
) -> None:
    tasks = build_tasks()

    # ========================================================
    # 第一次运行：
    # Q001 PASS
    # Q002 quota exhausted
    # Q003 不应该执行
    # ========================================================

    first_runner = FakeRunner(
        {
            "额度不足的问题": 1,
        }
    )

    first_batch = QwenBatchRunner(
        runner=first_runner,
        output_dir=tmp_path,
    )

    first_results = first_batch.run(
        tasks
    )

    assert first_runner.calls == [
        "已经完成的问题",
        "额度不足的问题",
    ]

    assert len(first_results) == 2

    assert (
        first_results[0].status
        == "pass"
    )

    assert (
        first_results[1].status
        == "blocked"
    )

    assert (
        tmp_path
        / "Q001_quick.json"
    ).exists()

    assert (
        tmp_path
        / "Q002_research_blocked.json"
    ).exists()

    assert not (
        tmp_path
        / "Q003_quick.json"
    ).exists()

    first_stdout = (
        capsys.readouterr().out
    )

    assert (
        "[QUOTA EXHAUSTED]"
        in first_stdout
    )

    assert (
        "[ACCOUNT SWITCH REQUIRED]"
        in first_stdout
    )

    first_summary = json.loads(
        (
            tmp_path
            / "batch_summary.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        first_summary["status"]
        == "blocked"
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

    # ========================================================
    # 模拟人工切换新账号：
    # 新账号不再触发 quota
    #
    # 使用同一个 output_dir + resume=True
    # ========================================================

    second_runner = FakeRunner()

    second_batch = QwenBatchRunner(
        runner=second_runner,
        output_dir=tmp_path,
    )

    second_results = second_batch.run(
        tasks,
        resume=True,
    )

    # Q001 已经 PASS，应直接跳过
    #
    # Q002 上次 BLOCKED，应重新执行
    # Q003 正常继续
    assert second_runner.calls == [
        "额度不足的问题",
        "额度后面的任务",
    ]

    assert len(second_results) == 3

    assert all(
        item.status == "pass"
        for item in second_results
    )

    assert (
        tmp_path
        / "Q002_research.json"
    ).exists()

    assert (
        tmp_path
        / "Q003_quick.json"
    ).exists()

    # 成功恢复以后，
    # 旧 blocked 文件应该被清掉
    assert not (
        tmp_path
        / "Q002_research_blocked.json"
    ).exists()

    second_stdout = (
        capsys.readouterr().out
    )

    assert (
        "[TASK SKIP] Q001 quick"
        in second_stdout
    )

    assert (
        "[REASON] already passed"
        in second_stdout
    )

    final_summary = json.loads(
        (
            tmp_path
            / "batch_summary.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        final_summary["status"]
        == "completed"
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
