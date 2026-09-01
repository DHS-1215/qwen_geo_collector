from __future__ import annotations

import pytest

from app.qwen.analysis.sentiment_aggregator import (
    aggregate_sentiment_results,
)
from app.qwen.analysis.sentiment_models import (
    SentimentResult,
)


def make_result(
    *,
    question_id: str,
    mode: str,
    sentiment: str | None,
    status: str = "success",
    planned: bool = True,
) -> SentimentResult:
    return SentimentResult(
        question_id=question_id,
        mode=mode,
        target_id="hongmao",
        classification_planned=planned,
        sentiment_status=status,
        final_sentiment=sentiment,
    )


def test_quick_non_negative_rate():
    result = (
        aggregate_sentiment_results(
            [
                make_result(
                    question_id="Q001",
                    mode="quick",
                    sentiment="positive",
                ),
                make_result(
                    question_id="Q002",
                    mode="quick",
                    sentiment="neutral",
                ),
                make_result(
                    question_id="Q003",
                    mode="quick",
                    sentiment="negative",
                ),
            ]
        )
    )

    summary = result.summaries[
        "hongmao"
    ].quick

    assert (
        summary.planned_mention_count
        == 3
    )

    assert (
        summary.classified_mention_count
        == 3
    )

    assert summary.positive_count == 1
    assert summary.neutral_count == 1
    assert summary.negative_count == 1

    assert (
        summary.non_negative_count
        == 2
    )

    assert (
        summary.non_negative_rate
        == pytest.approx(
            2 / 3
        )
    )


def test_quick_and_research_are_separate():
    result = (
        aggregate_sentiment_results(
            [
                make_result(
                    question_id="Q001",
                    mode="quick",
                    sentiment="positive",
                ),
                make_result(
                    question_id="Q001",
                    mode="research",
                    sentiment="negative",
                ),
            ]
        )
    )

    summary = result.summaries[
        "hongmao"
    ]

    assert (
        summary.quick.positive_count
        == 1
    )

    assert (
        summary.research.negative_count
        == 1
    )

    assert (
        summary.all_answers
        .classified_mention_count
        == 2
    )


def test_failed_classification_not_in_rate_denominator():
    result = (
        aggregate_sentiment_results(
            [
                make_result(
                    question_id="Q001",
                    mode="quick",
                    sentiment="positive",
                ),
                make_result(
                    question_id="Q002",
                    mode="quick",
                    sentiment=None,
                    status="failed",
                ),
            ]
        )
    )

    summary = result.summaries[
        "hongmao"
    ].quick

    assert (
        summary.planned_mention_count
        == 2
    )

    assert (
        summary.classified_mention_count
        == 1
    )

    assert (
        summary.classification_failed_count
        == 1
    )

    assert (
        summary.non_negative_rate
        == 1.0
    )


def test_not_applicable_is_not_planned():
    result = (
        aggregate_sentiment_results(
            [
                make_result(
                    question_id="Q001",
                    mode="quick",
                    sentiment=None,
                    status="not_applicable",
                    planned=False,
                )
            ]
        )
    )

    summary = result.summaries[
        "hongmao"
    ].quick

    assert (
        summary.planned_mention_count
        == 0
    )

    assert (
        summary.classified_mention_count
        == 0
    )


def test_zero_classified_has_zero_rates():
    result = (
        aggregate_sentiment_results(
            [
                make_result(
                    question_id="Q001",
                    mode="quick",
                    sentiment=None,
                    status="failed",
                )
            ]
        )
    )

    summary = result.summaries[
        "hongmao"
    ].quick

    assert summary.positive_rate == 0.0
    assert summary.neutral_rate == 0.0
    assert summary.negative_rate == 0.0

    assert (
        summary.non_negative_rate
        == 0.0
    )


def test_question_level_negative_has_priority():
    result = (
        aggregate_sentiment_results(
            [
                make_result(
                    question_id="Q001",
                    mode="quick",
                    sentiment="positive",
                ),
                make_result(
                    question_id="Q001",
                    mode="research",
                    sentiment="negative",
                ),
            ]
        )
    )

    summary = result.summaries[
        "hongmao"
    ].question_level

    assert (
        summary.planned_mention_count
        == 1
    )

    assert (
        summary.classified_mention_count
        == 1
    )

    assert summary.negative_count == 1
    assert summary.positive_count == 0


def test_question_level_positive_beats_neutral():
    result = (
        aggregate_sentiment_results(
            [
                make_result(
                    question_id="Q001",
                    mode="quick",
                    sentiment="neutral",
                ),
                make_result(
                    question_id="Q001",
                    mode="research",
                    sentiment="positive",
                ),
            ]
        )
    )

    summary = result.summaries[
        "hongmao"
    ].question_level

    assert summary.positive_count == 1
    assert summary.neutral_count == 0


def test_question_level_failed_only_question():
    result = (
        aggregate_sentiment_results(
            [
                make_result(
                    question_id="Q001",
                    mode="quick",
                    sentiment=None,
                    status="failed",
                ),
                make_result(
                    question_id="Q001",
                    mode="research",
                    sentiment=None,
                    status="timeout",
                ),
            ]
        )
    )

    summary = result.summaries[
        "hongmao"
    ].question_level

    assert (
        summary.planned_mention_count
        == 1
    )

    assert (
        summary.classified_mention_count
        == 0
    )

    assert (
        summary.classification_failed_count
        == 1
    )
