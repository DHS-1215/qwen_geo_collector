from __future__ import annotations

from app.qwen.answer_cleaning import (
    clean_qwen_answer_text,
)
from app.qwen.package.site_utils import (
    source_site_name_from_url,
)

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
# =============================================
# Central GEO package mapping
# =============================================

from typing import Literal

from app.qwen.package.central_models import (
    GeoPackageAnswer,
    GeoPackageSource,
    GeoPackageTask,
)


def qwen_mode_to_geo_mode(
        mode: str,
) -> Literal[
    "quick",
    "expert",
]:
    if mode == "quick":
        return "quick"

    if mode == "research":
        return "expert"

    raise ValueError(
        f"unsupported Qwen mode: {mode}"
    )


def qwen_task_status_to_geo_status(
        status: str,
) -> Literal[
    "success",
    "failed",
    "running",
]:
    if status == "pass":
        return "success"

    if status in {
        "fail",
        "blocked",
    }:
        return "failed"

    if status == "pending":
        return "running"

    raise ValueError(
        "unsupported Qwen task status: "
        f"{status}"
    )


def _build_stable_geo_id(
        prefix: str,
        *parts: str,
) -> str:
    raw = "|".join(
        str(part)
        for part in parts
    )

    digest = hashlib.sha1(
        raw.encode("utf-8")
    ).hexdigest()[:16]

    return (
        f"{prefix}_{digest}"
    )


def build_geo_task_id(
        *,
        batch_id: str,
        question_id: str,
        mode: str,
) -> str:
    return _build_stable_geo_id(
        "qwen_task",
        batch_id,
        question_id,
        mode,
    )


def build_geo_answer_id(
        *,
        task_id: str,
) -> str:
    return _build_stable_geo_id(
        "qwen_answer",
        task_id,
    )


def build_geo_source_occurrence_id(
        *,
        answer_id: str,
        source_order: int,
        url: str,
) -> str:
    return _build_stable_geo_id(
        "qwen_source",
        answer_id,
        str(source_order),
        url,
    )


def task_run_to_geo_task(
        task_result: QwenTaskRunResult,
        *,
        batch_id: str,
) -> GeoPackageTask:
    task_id = build_geo_task_id(
        batch_id=batch_id,
        question_id=(
            task_result.question_id
        ),
        mode=task_result.mode,
    )

    return GeoPackageTask(
        task_id=task_id,
        question_id=(
            task_result.question_id
        ),
        question=task_result.question,
        mode_code=qwen_mode_to_geo_mode(
            task_result.mode
        ),
        task_status=(
            qwen_task_status_to_geo_status(
                task_result.status
            )
        ),
        error_code=task_result.error_type,
        error_message=(
            task_result.error_message
        ),
    )


def answer_result_to_geo_answer(
        result: QwenAnswerResult,
        *,
        batch_id: str,
) -> GeoPackageAnswer:
    if result.question_id is None:
        raise ValueError(
            "QwenAnswerResult.question_id "
            "must not be None"
        )

    task_id = build_geo_task_id(
        batch_id=batch_id,
        question_id=result.question_id,
        mode=result.mode,
    )

    answer_id = build_geo_answer_id(
        task_id=task_id
    )

    raw_text = result.answer

    clean_text = clean_qwen_answer_text(
        raw_text,
        mode=result.mode,
    )

    return GeoPackageAnswer(
        answer_id=answer_id,
        task_id=task_id,
        question_id=result.question_id,
        mode_code=qwen_mode_to_geo_mode(
            result.mode
        ),
        question_text=result.question,
        answer_text_raw=raw_text,
        answer_text_clean=clean_text,
        acquisition_status="success",
        validation_status="PASS",
        is_complete=bool(
            clean_text
        ),
        source_collection_status=(
            "success"
        ),
        source_count_raw=len(
            result.sources
        ),
        screenshot_path=None,
        collected_at=result.acquired_at,
        platform_meta_json={
            "original_mode":
                result.mode,
            "mode_label":
                result.mode_label,
            "turn_id":
                result.turn_id,
            "chat_url":
                result.chat_url,
            "search_queries":
                list(
                    result.search_queries
                ),
            "citation_mapping_available":
                result.citation_mapping_available,
        },
    )


def answer_result_to_geo_sources(
        result: QwenAnswerResult,
        *,
        batch_id: str,
) -> list[GeoPackageSource]:
    if result.question_id is None:
        raise ValueError(
            "QwenAnswerResult.question_id "
            "must not be None"
        )

    task_id = build_geo_task_id(
        batch_id=batch_id,
        question_id=result.question_id,
        mode=result.mode,
    )

    answer_id = build_geo_answer_id(
        task_id=task_id
    )

    records: list[
        GeoPackageSource
    ] = []

    seen_urls: set[str] = set()

    for source in result.sources:
        url = source.url.strip()

        if not url:
            raise ValueError(
                "source URL must not be empty"
            )

        is_duplicate = (
            url in seen_urls
        )

        occurrence_id = (
            build_geo_source_occurrence_id(
                answer_id=answer_id,
                source_order=source.rank,
                url=url,
            )
        )

        records.append(
            GeoPackageSource(
                occurrence_id=(
                    occurrence_id
                ),
                answer_id=answer_id,
                source_order=source.rank,
                source_title_raw=(
                    source.title
                ),
                source_site_name_raw=(
                    source_site_name_from_url(
                        url
                    )
                ),
                source_url_raw=url,
                source_snippet=None,
                is_duplicate_in_answer=(
                    is_duplicate
                ),
            )
        )

        seen_urls.add(
            url
        )

    return records
