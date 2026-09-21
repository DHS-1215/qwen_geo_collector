from types import SimpleNamespace

import pytest

import app.qwen.batch as batch_module
from app.qwen.batch import QwenBatchRunner
from app.qwen.exceptions import (
    QwenQuotaExhaustedError,
)


class FakeRunner:
    def __init__(
        self,
        answers,
    ):
        self.answers = list(answers)
        self.calls = 0

    def ask(
        self,
        *args,
        **kwargs,
    ):
        answer = self.answers[
            self.calls
        ]
        self.calls += 1

        return SimpleNamespace(
            answer=answer,
        )


def make_task():
    return SimpleNamespace(
        question_id="Q001",
        question="测试问题",
        mode="research",
    )


def test_quota_exhausted_raises_immediately(
    tmp_path,
    monkeypatch,
):
    runner = FakeRunner(
        [
            "今日使用次数已达上限",
        ]
    )

    sleep_calls = []

    monkeypatch.setattr(
        batch_module.time,
        "sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
    )

    batch = QwenBatchRunner(
        runner,
        tmp_path,
    )

    with pytest.raises(
        QwenQuotaExhaustedError
    ):
        batch._ask_with_refusal_retry(
            make_task(),
            timeout_seconds=60,
        )

    assert runner.calls == 1
    assert sleep_calls == []


def test_quota_after_refusal_retry(
    tmp_path,
    monkeypatch,
):
    runner = FakeRunner(
        [
            (
                "你好，我无法回答这个问题，"
                "我们换一个话题聊聊吧。"
            ),
            "今日次数已用完",
        ]
    )

    sleep_calls = []

    monkeypatch.setattr(
        batch_module.time,
        "sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
    )

    batch = QwenBatchRunner(
        runner,
        tmp_path,
    )

    with pytest.raises(
        QwenQuotaExhaustedError
    ):
        batch._ask_with_refusal_retry(
            make_task(),
            timeout_seconds=60,
        )

    assert runner.calls == 2
    assert sleep_calls == [600]


def test_normal_answer_not_affected(
    tmp_path,
):
    runner = FakeRunner(
        [
            "这是一条正常回答。",
        ]
    )

    batch = QwenBatchRunner(
        runner,
        tmp_path,
    )

    result = (
        batch._ask_with_refusal_retry(
            make_task(),
            timeout_seconds=60,
        )
    )

    assert result.answer == (
        "这是一条正常回答。"
    )
    assert runner.calls == 1
