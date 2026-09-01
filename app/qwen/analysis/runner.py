from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

from app.qwen.analysis.mention_aggregator import (
    AnalysisItem,
    analyze_batch_mentions,
)
from app.qwen.analysis.models import (
    MentionBatchResult,
    MentionTarget,
)
from app.qwen.models import (
    QwenAnswerResult,
)
from app.qwen.package.reader import (
    load_answer_result,
    load_batch_summary,
)


def _resolve_answer_path(
    batch_dir: Path,
    output_path: str,
) -> Path:
    path = Path(output_path)

    if path.is_absolute():
        return path

    if path.exists():
        return path

    return (
        batch_dir
        / path.name
    )


def load_analysis_items(
    batch_dir: str | Path,
) -> list[AnalysisItem]:
    batch_dir = Path(batch_dir)

    summary = load_batch_summary(
        batch_dir
    )

    items: list[AnalysisItem] = []

    for task_result in summary.task_results:
        answer_result: (
            QwenAnswerResult | None
        ) = None

        if task_result.status == "pass":
            if not task_result.output_path:
                raise ValueError(
                    "pass task missing output_path: "
                    f"{task_result.question_id} "
                    f"{task_result.mode}"
                )

            answer_path = _resolve_answer_path(
                batch_dir,
                task_result.output_path,
            )

            answer_result = load_answer_result(
                answer_path
            )

        items.append(
            (
                task_result,
                answer_result,
            )
        )

    return items


def run_mention_analysis(
    batch_dir: str | Path,
    targets: Sequence[MentionTarget],
) -> MentionBatchResult:
    items = load_analysis_items(
        batch_dir
    )

    return analyze_batch_mentions(
        items,
        targets,
    )
