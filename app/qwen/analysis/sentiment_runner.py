from __future__ import annotations

from pathlib import Path

from app.qwen.analysis.mention import (
    analyze_target,
)
from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.runner import (
    load_analysis_items,
)
from app.qwen.analysis.sentiment import (
    SentimentClassifier,
    analyze_sentiment,
)
from app.qwen.analysis.sentiment_aggregator import (
    aggregate_sentiment_results,
)
from app.qwen.analysis.sentiment_models import (
    SentimentBatchResult,
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


async def analyze_batch_sentiment(
    *,
    items: list[AnalysisItem],
    targets: list[MentionTarget],
    classifier: SentimentClassifier,
) -> SentimentBatchResult:
    _validate_targets(
        targets
    )

    details = []

    for (
        task_result,
        answer_result,
    ) in items:
        is_valid = (
            is_valid_analysis_answer(
                task_result,
                answer_result,
            )
        )

        answer_text = (
            answer_result.answer
            if answer_result is not None
            else ""
        )

        for target in targets:
            mention = analyze_target(
                answer_text,
                target,
            )

            sentiment = await analyze_sentiment(
                question_id=(
                    task_result.question_id
                ),
                mode=task_result.mode,
                answer_text=answer_text,
                is_valid_answer=is_valid,
                mention=mention,
                target=target,
                classifier=classifier,
            )

            details.append(
                sentiment
            )

    return aggregate_sentiment_results(
        details
    )


async def run_sentiment_analysis(
    batch_dir: str | Path,
    targets: list[MentionTarget],
    classifier: SentimentClassifier,
) -> SentimentBatchResult:
    items = load_analysis_items(
        Path(batch_dir)
    )

    return await analyze_batch_sentiment(
        items=items,
        targets=targets,
        classifier=classifier,
    )


def _validate_targets(
    targets: list[MentionTarget],
) -> None:
    if not targets:
        raise ValueError(
            "sentiment targets cannot be empty"
        )

    seen: set[str] = set()

    for target in targets:
        target_id = (
            target.target_id.strip()
        )

        if not target_id:
            raise ValueError(
                "target_id cannot be empty"
            )

        if target_id in seen:
            raise ValueError(
                "duplicate sentiment target_id: "
                f"{target_id}"
            )

        seen.add(
            target_id
        )
