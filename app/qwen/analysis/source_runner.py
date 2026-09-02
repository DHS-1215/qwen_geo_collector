from __future__ import annotations

from pathlib import Path

from app.qwen.analysis.runner import (
    load_analysis_items,
)
from app.qwen.analysis.source_aggregator import (
    aggregate_source_occurrences,
)
from app.qwen.analysis.source_models import (
    SourceAnalysisResult,
    SourceOccurrence,
)
from app.qwen.analysis.source_normalization import (
    canonicalize_source_url,
    extract_source_domain,
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


def analyze_batch_sources(
    *,
    items: list[AnalysisItem],
) -> SourceAnalysisResult:
    occurrences: list[
        SourceOccurrence
    ] = []

    for (
        task_result,
        answer_result,
    ) in items:
        if not is_valid_analysis_answer(
            task_result,
            answer_result,
        ):
            continue

        if answer_result is None:
            continue

        for source in answer_result.sources:
            source_key = (
                canonicalize_source_url(
                    source.url
                )
            )

            if not source_key:
                continue

            domain = extract_source_domain(
                source_key
            )

            occurrences.append(
                SourceOccurrence(
                    question_id=(
                        task_result.question_id
                    ),
                    mode=task_result.mode,
                    source_key=source_key,
                    domain=domain,
                    title=source.title.strip(),
                    url=source.url.strip(),
                    rank=source.rank,
                )
            )

    return aggregate_source_occurrences(
        occurrences
    )


def run_source_analysis(
    batch_dir: str | Path,
) -> SourceAnalysisResult:
    items = load_analysis_items(
        Path(batch_dir)
    )

    return analyze_batch_sources(
        items=items
    )
