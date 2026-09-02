from __future__ import annotations

import asyncio

from app.qwen.analysis.models import (
    MentionResult,
    MentionTarget,
)
from app.qwen.analysis.sentiment import (
    analyze_sentiment,
)
from app.qwen.analysis.sentiment_errors import (
    SentimentProviderError,
)


def _target():
    return MentionTarget(
        target_id="hongmao",
        aliases=[
            "鸿茅药酒",
        ],
    )


def _mention():
    return MentionResult(
        target_id="hongmao",
        mention_count=1,
        mentioned=True,
    )


class ErrorClassifier:
    name = "fake"

    def __init__(
        self,
        error_type,
    ):
        self.error_type = (
            error_type
        )

    async def classify(
        self,
        *,
        answer_text,
        target,
    ):
        raise SentimentProviderError(
            self.error_type,
            "provider failed",
        )


def _run(
    error_type,
):
    return asyncio.run(
        analyze_sentiment(
            question_id="Q001",
            mode="quick",
            answer_text=(
                "鸿茅药酒测试内容"
            ),
            is_valid_answer=True,
            mention=_mention(),
            target=_target(),
            classifier=(
                ErrorClassifier(
                    error_type
                )
            ),
        )
    )


def test_rate_limit_status():
    result = _run(
        "rate_limit"
    )

    assert (
        result.sentiment_status
        == "rate_limited"
    )

    assert (
        result.error_type
        == "rate_limit"
    )


def test_timeout_status():
    result = _run(
        "timeout"
    )

    assert (
        result.sentiment_status
        == "timeout"
    )

    assert (
        result.error_type
        == "timeout"
    )


def test_other_provider_error_is_failed():
    result = _run(
        "invalid_response"
    )

    assert (
        result.sentiment_status
        == "failed"
    )

    assert (
        result.error_type
        == "invalid_response"
    )
