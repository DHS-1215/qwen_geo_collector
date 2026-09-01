from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.qwen.analysis.sentiment_models import (
    SentimentBatchResult,
    SentimentSummary,
)


def _serialize_summary(
    summary: SentimentSummary,
) -> dict[str, Any]:
    return {
        "planned_mention_count": (
            summary.planned_mention_count
        ),
        "classified_mention_count": (
            summary.classified_mention_count
        ),
        "classification_failed_count": (
            summary.classification_failed_count
        ),
        "positive_count": (
            summary.positive_count
        ),
        "neutral_count": (
            summary.neutral_count
        ),
        "negative_count": (
            summary.negative_count
        ),
        "non_negative_count": (
            summary.non_negative_count
        ),
        "positive_rate": (
            summary.positive_rate
        ),
        "neutral_rate": (
            summary.neutral_rate
        ),
        "negative_rate": (
            summary.negative_rate
        ),
        "non_negative_rate": (
            summary.non_negative_rate
        ),
    }


def serialize_sentiment_result(
    result: SentimentBatchResult,
) -> dict[str, Any]:
    targets: dict[
        str,
        dict[str, Any],
    ] = {}

    for (
        target_id,
        summary,
    ) in result.summaries.items():
        targets[target_id] = {
            "quick": _serialize_summary(
                summary.quick
            ),
            "research": _serialize_summary(
                summary.research
            ),
            "all_answers": (
                _serialize_summary(
                    summary.all_answers
                )
            ),
            "question_level": (
                _serialize_summary(
                    summary.question_level
                )
            ),
        }

    return {
        "targets": targets,
        "details": [
            item.model_dump()
            for item in result.details
        ],
    }


def serialize_sentiment_metrics(
    result: SentimentBatchResult,
) -> dict[str, Any]:
    targets: dict[
        str,
        dict[str, Any],
    ] = {}

    for (
        target_id,
        summary,
    ) in result.summaries.items():
        targets[target_id] = {
            "non_negative_rate": {
                "quick": (
                    summary.quick
                    .non_negative_rate
                ),
                "research": (
                    summary.research
                    .non_negative_rate
                ),
                "all": (
                    summary.all_answers
                    .non_negative_rate
                ),
                "question": (
                    summary.question_level
                    .non_negative_rate
                ),
            },
            "negative_rate": {
                "quick": (
                    summary.quick
                    .negative_rate
                ),
                "research": (
                    summary.research
                    .negative_rate
                ),
                "all": (
                    summary.all_answers
                    .negative_rate
                ),
                "question": (
                    summary.question_level
                    .negative_rate
                ),
            },
        }

    return {
        "targets": targets,
    }


def write_sentiment_result(
    result: SentimentBatchResult,
    output_path: str | Path,
) -> Path:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = (
        serialize_sentiment_result(
            result
        )
    )

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def write_sentiment_metrics(
    result: SentimentBatchResult,
    output_path: str | Path,
) -> Path:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = (
        serialize_sentiment_metrics(
            result
        )
    )

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path
