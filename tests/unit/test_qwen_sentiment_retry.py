from __future__ import annotations

import asyncio

import pytest

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment_errors import (
    SentimentProviderError,
)
from app.qwen.analysis.sentiment_retry import (
    RetryingSentimentClassifier,
)


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao",
        aliases=[
            "鸿茅药酒",
        ],
    )


class FlakyClassifier:
    name = "fake"

    def __init__(
        self,
        failures: int,
    ) -> None:
        self.failures = failures
        self.calls = 0

    async def classify(
        self,
        *,
        answer_text,
        target,
    ):
        self.calls += 1

        if (
            self.calls
            <= self.failures
        ):
            raise SentimentProviderError(
                "timeout",
                "request timed out",
            )

        return "neutral"


class FatalClassifier:
    name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    async def classify(
        self,
        *,
        answer_text,
        target,
    ):
        self.calls += 1

        raise SentimentProviderError(
            "invalid_response",
            "bad response",
        )


class UnknownErrorClassifier:
    name = "fake"

    def __init__(self) -> None:
        self.calls = 0

    async def classify(
        self,
        *,
        answer_text,
        target,
    ):
        self.calls += 1

        raise ValueError(
            "unexpected error"
        )


def test_retry_then_success():
    base = FlakyClassifier(
        failures=2
    )

    classifier = (
        RetryingSentimentClassifier(
            base,
            max_retries=2,
            retry_backoff_seconds=(),
        )
    )

    result = asyncio.run(
        classifier.classify(
            answer_text="测试",
            target=_target(),
        )
    )

    assert result == "neutral"
    assert base.calls == 3


def test_retry_exhausted():
    base = FlakyClassifier(
        failures=10
    )

    classifier = (
        RetryingSentimentClassifier(
            base,
            max_retries=2,
            retry_backoff_seconds=(),
        )
    )

    with pytest.raises(
        SentimentProviderError
    ) as exc_info:
        asyncio.run(
            classifier.classify(
                answer_text="测试",
                target=_target(),
            )
        )

    assert (
        exc_info.value.error_type
        == "timeout"
    )

    assert base.calls == 3


def test_non_retryable_error_is_not_retried():
    base = FatalClassifier()

    classifier = (
        RetryingSentimentClassifier(
            base,
            max_retries=5,
            retry_backoff_seconds=(),
        )
    )

    with pytest.raises(
        SentimentProviderError
    ):
        asyncio.run(
            classifier.classify(
                answer_text="测试",
                target=_target(),
            )
        )

    assert base.calls == 1


def test_unknown_exception_is_not_retried():
    base = UnknownErrorClassifier()

    classifier = (
        RetryingSentimentClassifier(
            base,
            max_retries=5,
            retry_backoff_seconds=(),
        )
    )

    with pytest.raises(
        ValueError
    ):
        asyncio.run(
            classifier.classify(
                answer_text="测试",
                target=_target(),
            )
        )

    assert base.calls == 1


def test_backoff_sequence_and_reuse(
    monkeypatch,
):
    base = FlakyClassifier(
        failures=3
    )

    delays = []

    async def fake_sleep(
        seconds,
    ):
        delays.append(
            seconds
        )

    monkeypatch.setattr(
        "app.qwen.analysis."
        "sentiment_retry."
        "asyncio.sleep",
        fake_sleep,
    )

    classifier = (
        RetryingSentimentClassifier(
            base,
            max_retries=3,
            retry_backoff_seconds=(
                1.0,
                2.0,
            ),
        )
    )

    result = asyncio.run(
        classifier.classify(
            answer_text="测试",
            target=_target(),
        )
    )

    assert result == "neutral"

    assert delays == [
        1.0,
        2.0,
        2.0,
    ]


def test_provider_error_retryable_flag():
    assert (
        SentimentProviderError(
            "rate_limit",
            "429",
        ).retryable
        is True
    )

    assert (
        SentimentProviderError(
            "network_error",
            "network",
        ).retryable
        is True
    )

    assert (
        SentimentProviderError(
            "invalid_response",
            "bad json",
        ).retryable
        is False
    )
