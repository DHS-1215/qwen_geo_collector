from __future__ import annotations

import hashlib

from app.qwen.models import (
    QwenAnswerResult,
    QwenTaskRunResult,
)
from app.qwen.package.models import (
    QwenPackageAnswer,
    QwenPackageSource,
    QwenPackageTask,
)


def task_run_to_package_task(
        task_result: QwenTaskRunResult,
) -> QwenPackageTask:
    return QwenPackageTask(
        question_id=task_result.question_id,
        question=task_result.question,
        mode=task_result.mode,
        status=task_result.status,
        error_type=task_result.error_type,
        error_message=task_result.error_message,
    )


def answer_result_to_package_answer(
        result: QwenAnswerResult,
) -> QwenPackageAnswer:
    if result.question_id is None:
        raise ValueError(
            "QwenAnswerResult.question_id "
            "must not be None"
        )

    return QwenPackageAnswer(
        question_id=result.question_id,
        question=result.question,
        mode=result.mode,
        mode_label=result.mode_label,
        answer=result.answer,
        turn_id=result.turn_id,
        chat_url=result.chat_url,
        search_queries=result.search_queries,
        citation_mapping_available=(
            result.citation_mapping_available
        ),
        acquired_at=result.acquired_at,
    )


def build_source_occurrence_id(
        *,
        question_id: str,
        mode: str,
        rank: int,
        url: str,
) -> str:
    raw = (
        f"{question_id}|"
        f"{mode}|"
        f"{rank}|"
        f"{url}"
    )

    return hashlib.sha1(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()[:12]


def answer_result_to_package_sources(
        result: QwenAnswerResult,
) -> list[QwenPackageSource]:
    if result.question_id is None:
        raise ValueError(
            "QwenAnswerResult.question_id "
            "must not be None"
        )

    sources: list[
        QwenPackageSource
    ] = []

    for source in result.sources:
        occurrence_id = (
            build_source_occurrence_id(
                question_id=(
                    result.question_id
                ),
                mode=result.mode,
                rank=source.rank,
                url=source.url,
            )
        )

        sources.append(
            QwenPackageSource(
                occurrence_id=(
                    occurrence_id
                ),
                question_id=(
                    result.question_id
                ),
                mode=result.mode,
                rank=source.rank,
                title=source.title,
                url=source.url,
            )
        )

    return sources