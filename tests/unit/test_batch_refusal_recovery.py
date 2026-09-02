from __future__ import annotations

import json
from pathlib import Path

import app.qwen.batch as batch_module
from app.qwen.batch import (
    REFUSAL_RETRY_WAIT_SECONDS,
    QwenBatchRunner,
)
from app.qwen.models import (
    QwenAnswerResult,
)
from app.qwen.tasks import (
    QwenTask,
)


REFUSAL_TEXT = (
    "你好，我无法回答这个问题，"
    "我们换一个话题聊聊吧。"
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
        refusal_remaining: dict[str, int] | None = None,
    ) -> None:
        self.page = FakePage()
        self.calls: list[str] = []
        self.refusal_remaining = dict(
            refusal_remaining or {}
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
            self.refusal_remaining.get(
                question,
                0,
            )
        )

        if remaining > 0:
            self.refusal_remaining[
                question
            ] = remaining - 1

            answer = REFUSAL_TEXT

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


def test_normal_answer_does_not_retry(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sleep_calls: list[int] = []

    monkeypatch.setattr(
        batch_module.time,
        "sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
    )

    runner = FakeRunner()

    batch = QwenBatchRunner(
        runner=runner,
        output_dir=tmp_path,
    )

    results = batch.run(
        [
            QwenTask(
                question_id="Q001",
                question="正常问题",
                mode="quick",
            )
        ]
    )

    assert runner.calls == [
        "正常问题"
    ]

    assert sleep_calls == []

    assert len(results) == 1
    assert results[0].status == "pass"

    assert (
        tmp_path
        / "Q001_quick.json"
    ).exists()


def test_refusal_retries_after_wait_and_recovers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sleep_calls: list[int] = []

    monkeypatch.setattr(
        batch_module.time,
        "sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
    )

    runner = FakeRunner(
        {
            "拒答测试": 1,
        }
    )

    batch = QwenBatchRunner(
        runner=runner,
        output_dir=tmp_path,
    )

    results = batch.run(
        [
            QwenTask(
                question_id="Q001",
                question="拒答测试",
                mode="quick",
            )
        ]
    )

    assert runner.calls == [
        "拒答测试",
        "拒答测试",
    ]

    assert sleep_calls == [
        REFUSAL_RETRY_WAIT_SECONDS
    ]

    assert len(results) == 1
    assert results[0].status == "pass"

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

    assert (
        data["answer"]
        == "正常回答：拒答测试"
    )

    assert not (
        tmp_path
        / "Q001_quick_blocked.json"
    ).exists()


def test_persistent_refusal_blocks_batch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sleep_calls: list[int] = []

    monkeypatch.setattr(
        batch_module.time,
        "sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
    )

    runner = FakeRunner(
        {
            "拒答测试": 2,
        }
    )

    batch = QwenBatchRunner(
        runner=runner,
        output_dir=tmp_path,
    )

    tasks = [
        QwenTask(
            question_id="Q001",
            question="拒答测试",
            mode="quick",
        ),
        QwenTask(
            question_id="Q002",
            question="不应该执行",
            mode="quick",
        ),
    ]

    results = batch.run(
        tasks
    )

    assert runner.calls == [
        "拒答测试",
        "拒答测试",
    ]

    assert sleep_calls == [
        REFUSAL_RETRY_WAIT_SECONDS
    ]

    assert len(results) == 1

    assert (
        results[0].status
        == "blocked"
    )

    assert (
        results[0].error_type
        == "QwenRefusalError"
    )

    assert not (
        tmp_path
        / "Q001_quick.json"
    ).exists()

    assert (
        tmp_path
        / "Q001_quick_blocked.json"
    ).exists()

    assert not (
        tmp_path
        / "Q002_quick.json"
    ).exists()

    summary = json.loads(
        (
            tmp_path
            / "batch_summary.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        summary["status"]
        == "blocked"
    )

    assert (
        summary["executed_count"]
        == 1
    )

    assert (
        summary["blocked_count"]
        == 1
    )

    assert (
        summary["pending_count"]
        == 1
    )


def test_resume_retries_blocked_refusal_task(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        batch_module.time,
        "sleep",
        lambda seconds: None,
    )

    runner = FakeRunner(
        {
            "拒答测试": 2,
        }
    )

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
            question="拒答测试",
            mode="quick",
        ),
        QwenTask(
            question_id="Q003",
            question="正常问题2",
            mode="quick",
        ),
    ]

    first_results = batch.run(
        tasks
    )

    assert [
        item.status
        for item in first_results
    ] == [
        "pass",
        "blocked",
    ]

    assert runner.calls == [
        "正常问题1",
        "拒答测试",
        "拒答测试",
    ]

    second_results = batch.run(
        tasks,
        resume=True,
    )

    assert runner.calls == [
        "正常问题1",
        "拒答测试",
        "拒答测试",
        "拒答测试",
        "正常问题2",
    ]

    assert (
        runner.calls.count(
            "正常问题1"
        )
        == 1
    )

    assert len(second_results) == 3

    assert all(
        item.status == "pass"
        for item in second_results
    )

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

    assert not (
        tmp_path
        / "Q002_quick_blocked.json"
    ).exists()

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
        final_summary["blocked_count"]
        == 0
    )

    assert (
        final_summary["pending_count"]
        == 0
    )
