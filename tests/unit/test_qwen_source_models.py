from __future__ import annotations

from app.qwen.analysis.source_models import (
    SourceAnalysisResult,
    SourceOccurrence,
    SourceRankItem,
    SourceSummary,
)


def test_source_occurrence():
    item = SourceOccurrence(
        question_id="Q001",
        mode="quick",
        source_key=(
            "https://example.com/a"
        ),
        domain="example.com",
        title="测试来源",
        url=(
            "https://example.com/a"
        ),
        rank=1,
    )

    assert item.rank == 1
    assert (
        item.domain
        == "example.com"
    )


def test_source_rank_item():
    item = SourceRankItem(
        source_key=(
            "https://example.com/a"
        ),
        domain="example.com",
        title="测试来源",
        url=(
            "https://example.com/a"
        ),
        occurrence_count=3,
        question_count=2,
        average_order=1.5,
        first_seen_order=1,
        share=0.5,
    )

    assert (
        item.occurrence_count
        == 3
    )

    assert item.share == 0.5


def test_source_summary_defaults():
    summary = SourceSummary()

    assert (
        summary.total_occurrences
        == 0
    )

    assert (
        summary.top10_share
        == 0.0
    )

    assert (
        summary.top_sources
        == []
    )


def test_source_analysis_result_defaults():
    result = SourceAnalysisResult()

    assert result.occurrences == []

    assert (
        result.quick
        .total_occurrences
        == 0
    )

    assert (
        result.research
        .total_occurrences
        == 0
    )

    assert (
        result.all_sources
        .total_occurrences
        == 0
    )
