from __future__ import annotations

from typing import Any

from app.qwen.analysis.models import (
    MentionBatchResult,
    MentionSummary,
)


def _serialize_summary(
    summary: MentionSummary,
) -> dict[str, int | float]:
    return {
        "valid_count": summary.valid_count,
        "mentioned_count": summary.mentioned_count,
        "mention_rate": summary.mention_rate,
    }


def serialize_mention_result(
    result: MentionBatchResult,
) -> dict[str, Any]:
    targets: dict[str, Any] = {}

    for target_id in sorted(
        result.summaries
    ):
        summary = result.summaries[
            target_id
        ]

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
            detail.model_dump()
            for detail in result.details
        ],
    }


def serialize_mention_metrics(
    result: MentionBatchResult,
) -> dict[str, Any]:
    targets: dict[str, Any] = {}

    for target_id in sorted(
        result.summaries
    ):
        summary = result.summaries[
            target_id
        ]

        targets[target_id] = {
            "mention_rate": {
                "quick": (
                    summary.quick.mention_rate
                ),
                "research": (
                    summary.research.mention_rate
                ),
                "all": (
                    summary.all_answers.mention_rate
                ),
                "question": (
                    summary.question_level.mention_rate
                ),
            }
        }

    return {
        "targets": targets,
    }
