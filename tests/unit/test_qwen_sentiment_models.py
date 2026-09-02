from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.qwen.analysis.sentiment_models import (
    SentimentResult,
    SentimentSummary,
)


def test_sentiment_result_accepts_positive():
    result = SentimentResult(
        question_id="Q001",
        mode="quick",
        target_id="hongmao",
        classification_planned=True,
        sentiment_status="success",
        model_sentiment="positive",
        final_sentiment="positive",
    )

    assert (
        result.final_sentiment
        == "positive"
    )


def test_sentiment_result_accepts_neutral():
    result = SentimentResult(
        question_id="Q001",
        mode="quick",
        target_id="hongmao",
        classification_planned=True,
        sentiment_status="success",
        final_sentiment="neutral",
    )

    assert (
        result.final_sentiment
        == "neutral"
    )


def test_sentiment_result_accepts_negative():
    result = SentimentResult(
        question_id="Q001",
        mode="quick",
        target_id="hongmao",
        classification_planned=True,
        sentiment_status="success",
        final_sentiment="negative",
    )

    assert (
        result.final_sentiment
        == "negative"
    )


def test_sentiment_result_rejects_invalid_label():
    with pytest.raises(
        ValidationError
    ):
        SentimentResult(
            question_id="Q001",
            mode="quick",
            target_id="hongmao",
            classification_planned=True,
            sentiment_status="success",
            final_sentiment="mixed",
        )


def test_not_applicable_can_have_no_sentiment():
    result = SentimentResult(
        question_id="Q001",
        mode="quick",
        target_id="hongmao",
        classification_planned=False,
        sentiment_status=(
            "not_applicable"
        ),
    )

    assert (
        result.final_sentiment
        is None
    )


def test_summary_defaults_to_zero():
    summary = SentimentSummary()

    assert (
        summary.non_negative_count
        == 0
    )

    assert (
        summary.non_negative_rate
        == 0.0
    )
