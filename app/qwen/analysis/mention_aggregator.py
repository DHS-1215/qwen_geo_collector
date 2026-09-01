from __future__ import annotations

from collections.abc import Sequence

from app.qwen.analysis.mention import (
    analyze_target,
)
from app.qwen.analysis.models import (
    MentionBatchResult,
    MentionDetail,
    MentionSummary,
    MentionTarget,
    TargetMentionSummary,
)
from app.qwen.analysis.validity import (
    is_valid_analysis_answer,
)
from app.qwen.models import (
    QwenAnswerResult,
    QwenTaskRunResult,
)


AnalysisItem = tuple[
    QwenTaskRunResult,
    QwenAnswerResult | None,
]


def _build_summary(
    valid_count: int,
    mentioned_count: int,
) -> MentionSummary:
    mention_rate = 0.0

    if valid_count > 0:
        mention_rate = (
            mentioned_count
            / valid_count
        )

    return MentionSummary(
        valid_count=valid_count,
        mentioned_count=mentioned_count,
        mention_rate=mention_rate,
    )


def _answer_summary(
    details: Sequence[MentionDetail],
    mode: str | None = None,
) -> MentionSummary:
    selected = [
        detail
        for detail in details
        if (
            mode is None
            or detail.mode == mode
        )
    ]

    mentioned_count = sum(
        1
        for detail in selected
        if detail.mentioned
    )

    return _build_summary(
        valid_count=len(selected),
        mentioned_count=mentioned_count,
    )


def _question_summary(
    details: Sequence[MentionDetail],
) -> MentionSummary:
    valid_questions = {
        detail.question_id
        for detail in details
    }

    mentioned_questions = {
        detail.question_id
        for detail in details
        if detail.mentioned
    }

    return _build_summary(
        valid_count=len(valid_questions),
        mentioned_count=len(
            mentioned_questions
        ),
    )


def analyze_batch_mentions(
    items: Sequence[AnalysisItem],
    targets: Sequence[MentionTarget],
) -> MentionBatchResult:
    details: list[MentionDetail] = []

    for task_result, answer_result in items:
        if not is_valid_analysis_answer(
            task_result,
            answer_result,
        ):
            continue

        assert answer_result is not None

        for target in targets:
            result = analyze_target(
                answer_result.answer,
                target,
            )

            details.append(
                MentionDetail(
                    question_id=(
                        task_result.question_id
                    ),
                    mode=task_result.mode,
                    target_id=target.target_id,
                    mention_count=(
                        result.mention_count
                    ),
                    mentioned=result.mentioned,
                )
            )

    summaries: dict[
        str,
        TargetMentionSummary,
    ] = {}

    for target in targets:
        target_details = [
            detail
            for detail in details
            if (
                detail.target_id
                == target.target_id
            )
        ]

        summaries[target.target_id] = (
            TargetMentionSummary(
                target_id=target.target_id,
                quick=_answer_summary(
                    target_details,
                    mode="quick",
                ),
                research=_answer_summary(
                    target_details,
                    mode="research",
                ),
                all_answers=_answer_summary(
                    target_details,
                ),
                question_level=(
                    _question_summary(
                        target_details
                    )
                ),
            )
        )

    return MentionBatchResult(
        details=details,
        summaries=summaries,
    )
