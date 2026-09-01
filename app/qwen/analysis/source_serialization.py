from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.qwen.analysis.source_models import (
    HostSummary,
    SourceAnalysisResult,
    SourceSummary,
)


def _serialize_source_summary(
    summary: SourceSummary,
) -> dict[str, Any]:
    return {
        "total_occurrences": (
            summary.total_occurrences
        ),
        "unique_source_count": (
            summary.unique_source_count
        ),
        "top10_occurrences": (
            summary.top10_occurrences
        ),
        "top10_share": (
            summary.top10_share
        ),
        "top_sources": [
            item.model_dump()
            for item in summary.top_sources
        ],
    }


def _serialize_host_summary(
    summary: HostSummary,
) -> dict[str, Any]:
    return {
        "total_occurrences": (
            summary.total_occurrences
        ),
        "unique_host_count": (
            summary.unique_host_count
        ),
        "top10_occurrences": (
            summary.top10_occurrences
        ),
        "top10_share": (
            summary.top10_share
        ),
        "top_hosts": [
            item.model_dump()
            for item in summary.top_hosts
        ],
    }


def serialize_source_result(
    result: SourceAnalysisResult,
) -> dict[str, Any]:
    return {
        "url_level": {
            "quick": (
                _serialize_source_summary(
                    result.quick
                )
            ),
            "research": (
                _serialize_source_summary(
                    result.research
                )
            ),
            "all": (
                _serialize_source_summary(
                    result.all_sources
                )
            ),
        },
        "host_level": {
            "quick": (
                _serialize_host_summary(
                    result.quick_hosts
                )
            ),
            "research": (
                _serialize_host_summary(
                    result.research_hosts
                )
            ),
            "all": (
                _serialize_host_summary(
                    result.all_hosts
                )
            ),
        },
        "occurrences": [
            item.model_dump()
            for item in result.occurrences
        ],
    }


def serialize_source_metrics(
    result: SourceAnalysisResult,
) -> dict[str, Any]:
    return {
        "source_top10_share": {
            "quick": (
                result.quick.top10_share
            ),
            "research": (
                result.research.top10_share
            ),
            "all": (
                result.all_sources
                .top10_share
            ),
        },
        "host_top10_share": {
            "quick": (
                result.quick_hosts
                .top10_share
            ),
            "research": (
                result.research_hosts
                .top10_share
            ),
            "all": (
                result.all_hosts
                .top10_share
            ),
        },
        "source_occurrences": {
            "quick": (
                result.quick
                .total_occurrences
            ),
            "research": (
                result.research
                .total_occurrences
            ),
            "all": (
                result.all_sources
                .total_occurrences
            ),
        },
        "unique_sources": {
            "quick": (
                result.quick
                .unique_source_count
            ),
            "research": (
                result.research
                .unique_source_count
            ),
            "all": (
                result.all_sources
                .unique_source_count
            ),
        },
        "unique_hosts": {
            "quick": (
                result.quick_hosts
                .unique_host_count
            ),
            "research": (
                result.research_hosts
                .unique_host_count
            ),
            "all": (
                result.all_hosts
                .unique_host_count
            ),
        },
    }


def write_source_result(
    result: SourceAnalysisResult,
    output_path: str | Path,
) -> Path:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            serialize_source_result(
                result
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def write_source_metrics(
    result: SourceAnalysisResult,
    output_path: str | Path,
) -> Path:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            serialize_source_metrics(
                result
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path
