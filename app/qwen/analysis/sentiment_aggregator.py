from __future__ import annotations

from collections import defaultdict

from app.qwen.analysis.sentiment_models import (
    SentimentBatchResult,
    SentimentResult,
    SentimentSummary,
    TargetSentimentSummary,
)


SUCCESS_STATUSES = {
    "success",
    "success_with_warnings",
}

SENTIMENT_LABELS = {
    "positive",
    "neutral",
    "negative",
}


def _is_classified(
    item: SentimentResult,
) -> bool:
    return (
        item.classification_planned
        and item.sentiment_status
        in SUCCESS_STATUSES
        and item.final_sentiment
        in SENTIMENT_LABELS
    )


def _build_summary(
    items: list[SentimentResult],
) -> SentimentSummary:
    planned_items = [
        item
        for item in items
        if item.classification_planned
    ]

    classified_items = [
        item
        for item in planned_items
        if _is_classified(item)
    ]

    positive_count = sum(
        item.final_sentiment
        == "positive"
        for item in classified_items
    )

    neutral_count = sum(
        item.final_sentiment
        == "neutral"
        for item in classified_items
    )

    negative_count = sum(
        item.final_sentiment
        == "negative"
        for item in classified_items
    )

    planned_count = len(
        planned_items
    )

    classified_count = len(
        classified_items
    )

    failed_count = (
        planned_count
        - classified_count
    )

    non_negative_count = (
        positive_count
        + neutral_count
    )

    if classified_count == 0:
        positive_rate = 0.0
        neutral_rate = 0.0
        negative_rate = 0.0
        non_negative_rate = 0.0

    else:
        positive_rate = (
            positive_count
            / classified_count
        )

        neutral_rate = (
            neutral_count
            / classified_count
        )

        negative_rate = (
            negative_count
            / classified_count
        )

        non_negative_rate = (
            non_negative_count
            / classified_count
        )

    return SentimentSummary(
        planned_mention_count=(
            planned_count
        ),
        classified_mention_count=(
            classified_count
        ),
        classification_failed_count=(
            failed_count
        ),
        positive_count=(
            positive_count
        ),
        neutral_count=(
            neutral_count
        ),
        negative_count=(
            negative_count
        ),
        non_negative_count=(
            non_negative_count
        ),
        positive_rate=(
            positive_rate
        ),
        neutral_rate=(
            neutral_rate
        ),
        negative_rate=(
            negative_rate
        ),
        non_negative_rate=(
            non_negative_rate
        ),
    )


def _resolve_question_sentiment(
    items: list[SentimentResult],
) -> str | None:
    labels = {
        item.final_sentiment
        for item in items
        if _is_classified(item)
    }

    if "negative" in labels:
        return "negative"

    if "positive" in labels:
        return "positive"

    if "neutral" in labels:
        return "neutral"

    return None


def _build_question_summary(
    items: list[SentimentResult],
) -> SentimentSummary:
    planned_items = [
        item
        for item in items
        if item.classification_planned
    ]

    grouped: dict[
        str,
        list[SentimentResult],
    ] = defaultdict(list)

    for item in planned_items:
        grouped[
            item.question_id
        ].append(item)

    planned_count = len(
        grouped
    )

    positive_count = 0
    neutral_count = 0
    negative_count = 0

    for question_items in (
        grouped.values()
    ):
        label = (
            _resolve_question_sentiment(
                question_items
            )
        )

        if label == "positive":
            positive_count += 1

        elif label == "neutral":
            neutral_count += 1

        elif label == "negative":
            negative_count += 1

    classified_count = (
        positive_count
        + neutral_count
        + negative_count
    )

    failed_count = (
        planned_count
        - classified_count
    )

    non_negative_count = (
        positive_count
        + neutral_count
    )

    if classified_count == 0:
        positive_rate = 0.0
        neutral_rate = 0.0
        negative_rate = 0.0
        non_negative_rate = 0.0

    else:
        positive_rate = (
            positive_count
            / classified_count
        )

        neutral_rate = (
            neutral_count
            / classified_count
        )

        negative_rate = (
            negative_count
            / classified_count
        )

        non_negative_rate = (
            non_negative_count
            / classified_count
        )

    return SentimentSummary(
        planned_mention_count=(
            planned_count
        ),
        classified_mention_count=(
            classified_count
        ),
        classification_failed_count=(
            failed_count
        ),
        positive_count=(
            positive_count
        ),
        neutral_count=(
            neutral_count
        ),
        negative_count=(
            negative_count
        ),
        non_negative_count=(
            non_negative_count
        ),
        positive_rate=(
            positive_rate
        ),
        neutral_rate=(
            neutral_rate
        ),
        negative_rate=(
            negative_rate
        ),
        non_negative_rate=(
            non_negative_rate
        ),
    )


def aggregate_sentiment_results(
    details: list[SentimentResult],
) -> SentimentBatchResult:
    by_target: dict[
        str,
        list[SentimentResult],
    ] = defaultdict(list)

    for item in details:
        by_target[
            item.target_id
        ].append(item)

    summaries: dict[
        str,
        TargetSentimentSummary,
    ] = {}

    for (
        target_id,
        target_items,
    ) in by_target.items():
        quick_items = [
            item
            for item in target_items
            if item.mode == "quick"
        ]

        research_items = [
            item
            for item in target_items
            if item.mode == "research"
        ]

        summaries[
            target_id
        ] = TargetSentimentSummary(
            target_id=target_id,
            quick=_build_summary(
                quick_items
            ),
            research=_build_summary(
                research_items
            ),
            all_answers=_build_summary(
                target_items
            ),
            question_level=(
                _build_question_summary(
                    target_items
                )
            ),
        )

    return SentimentBatchResult(
        details=details,
        summaries=summaries,
    )
