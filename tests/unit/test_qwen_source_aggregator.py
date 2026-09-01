from __future__ import annotations

import pytest

from app.qwen.analysis.source_aggregator import (
    aggregate_source_occurrences,
)
from app.qwen.analysis.source_models import (
    SourceOccurrence,
)


def make_source(
        *,
        question_id: str,
        mode: str,
        source_key: str,
        rank: int = 1,
) -> SourceOccurrence:
    return SourceOccurrence(
        question_id=question_id,
        mode=mode,
        source_key=source_key,
        domain="example.com",
        title=source_key,
        url=source_key,
        rank=rank,
    )


def test_same_source_in_same_answer_is_deduplicated():
    source = (
        "https://example.com/a"
    )

    result = (
        aggregate_source_occurrences(
            [
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source,
                    rank=1,
                ),
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source,
                    rank=2,
                ),
            ]
        )
    )

    assert (
            result.quick.total_occurrences
            == 1
    )

    assert (
            result.quick.unique_source_count
            == 1
    )

    assert (
            result.quick.top_sources[0]
            .occurrence_count
            == 1
    )


def test_same_source_in_different_answers_counts_twice():
    source = (
        "https://example.com/a"
    )

    result = (
        aggregate_source_occurrences(
            [
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source,
                ),
                make_source(
                    question_id="Q002",
                    mode="quick",
                    source_key=source,
                ),
            ]
        )
    )

    item = (
        result.quick.top_sources[0]
    )

    assert (
            item.occurrence_count
            == 2
    )

    assert (
            item.question_count
            == 2
    )


def test_quick_and_research_are_separate():
    source = (
        "https://example.com/a"
    )

    result = (
        aggregate_source_occurrences(
            [
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source,
                ),
                make_source(
                    question_id="Q001",
                    mode="research",
                    source_key=source,
                ),
            ]
        )
    )

    assert (
            result.quick.total_occurrences
            == 1
    )

    assert (
            result.research
            .total_occurrences
            == 1
    )

    assert (
            result.all_sources
            .total_occurrences
            == 2
    )

    all_item = (
        result.all_sources
        .top_sources[0]
    )

    assert (
            all_item.occurrence_count
            == 2
    )

    # 同一个 question_id，
    # Quick + Research 仍只对应一个问题。
    assert (
            all_item.question_count
            == 1
    )


def test_source_share_uses_total_occurrences():
    source_a = (
        "https://example.com/a"
    )

    source_b = (
        "https://example.com/b"
    )

    result = (
        aggregate_source_occurrences(
            [
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source_a,
                ),
                make_source(
                    question_id="Q002",
                    mode="quick",
                    source_key=source_a,
                ),
                make_source(
                    question_id="Q003",
                    mode="quick",
                    source_key=source_b,
                ),
            ]
        )
    )

    items = {
        item.source_key: item
        for item in (
            result.quick.top_sources
        )
    }

    assert (
            items[source_a].share
            == pytest.approx(
        2 / 3
    )
    )

    assert (
            items[source_b].share
            == pytest.approx(
        1 / 3
    )
    )


def test_top10_share():
    occurrences = []

    for index in range(12):
        occurrences.append(
            make_source(
                question_id=(
                    f"Q{index:03d}"
                ),
                mode="quick",
                source_key=(
                    "https://example.com/"
                    f"{index}"
                ),
            )
        )

    result = (
        aggregate_source_occurrences(
            occurrences
        )
    )

    summary = result.quick

    assert (
            summary.total_occurrences
            == 12
    )

    assert (
            summary.unique_source_count
            == 12
    )

    assert (
            len(summary.top_sources)
            == 10
    )

    assert (
            summary.top10_occurrences
            == 10
    )

    assert (
            summary.top10_share
            == pytest.approx(
        10 / 12
    )
    )


def test_occurrence_count_has_highest_priority():
    source_a = (
        "https://example.com/a"
    )

    source_b = (
        "https://example.com/b"
    )

    result = (
        aggregate_source_occurrences(
            [
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source_a,
                    rank=5,
                ),
                make_source(
                    question_id="Q002",
                    mode="quick",
                    source_key=source_a,
                    rank=5,
                ),
                make_source(
                    question_id="Q003",
                    mode="quick",
                    source_key=source_b,
                    rank=1,
                ),
            ]
        )
    )

    assert (
            result.quick
            .top_sources[0]
            .source_key
            == source_a
    )


def test_question_count_breaks_occurrence_tie():
    source_a = (
        "https://example.com/a"
    )

    source_b = (
        "https://example.com/b"
    )

    result = (
        aggregate_source_occurrences(
            [
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source_a,
                    rank=5,
                ),
                make_source(
                    question_id="Q002",
                    mode="quick",
                    source_key=source_a,
                    rank=5,
                ),
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source_b,
                    rank=1,
                ),
                make_source(
                    question_id="Q001",
                    mode="research",
                    source_key=source_b,
                    rank=1,
                ),
            ]
        )
    )

    first = (
        result.all_sources
        .top_sources[0]
    )

    assert (
            first.source_key
            == source_a
    )

    assert (
            first.question_count
            == 2
    )


def test_average_order_breaks_tie():
    source_a = (
        "https://example.com/a"
    )

    source_b = (
        "https://example.com/b"
    )

    result = (
        aggregate_source_occurrences(
            [
                make_source(
                    question_id="Q001",
                    mode="quick",
                    source_key=source_a,
                    rank=3,
                ),
                make_source(
                    question_id="Q002",
                    mode="quick",
                    source_key=source_a,
                    rank=3,
                ),
                make_source(
                    question_id="Q003",
                    mode="quick",
                    source_key=source_b,
                    rank=1,
                ),
                make_source(
                    question_id="Q004",
                    mode="quick",
                    source_key=source_b,
                    rank=1,
                ),
            ]
        )
    )

    assert (
            result.quick
            .top_sources[0]
            .source_key
            == source_b
    )


def test_empty_occurrences():
    result = (
        aggregate_source_occurrences(
            []
        )
    )

    assert (
            result.quick.total_occurrences
            == 0
    )

    assert (
            result.quick.top10_share
            == 0.0
    )

    assert (
            result.all_sources
            .top_sources
            == []
    )


def test_same_host_different_urls_are_aggregated():
    result = (
        aggregate_source_occurrences(
            [
                SourceOccurrence(
                    question_id="Q001",
                    mode="quick",
                    source_key=(
                        "https://example.com/a"
                    ),
                    domain="example.com",
                    title="A",
                    url=(
                        "https://example.com/a"
                    ),
                    rank=1,
                ),
                SourceOccurrence(
                    question_id="Q002",
                    mode="quick",
                    source_key=(
                        "https://example.com/b"
                    ),
                    domain="example.com",
                    title="B",
                    url=(
                        "https://example.com/b"
                    ),
                    rank=1,
                ),
            ]
        )
    )

    host = (
        result.quick_hosts
        .top_hosts[0]
    )

    assert (
            host.host
            == "example.com"
    )

    assert (
            host.occurrence_count
            == 2
    )

    assert (
            host.question_count
            == 2
    )


def test_host_share_uses_all_occurrences():
    result = (
        aggregate_source_occurrences(
            [
                SourceOccurrence(
                    question_id="Q001",
                    mode="quick",
                    source_key="https://a.com/1",
                    domain="a.com",
                    title="A1",
                    url="https://a.com/1",
                    rank=1,
                ),
                SourceOccurrence(
                    question_id="Q002",
                    mode="quick",
                    source_key="https://a.com/2",
                    domain="a.com",
                    title="A2",
                    url="https://a.com/2",
                    rank=1,
                ),
                SourceOccurrence(
                    question_id="Q003",
                    mode="quick",
                    source_key="https://b.com/1",
                    domain="b.com",
                    title="B1",
                    url="https://b.com/1",
                    rank=1,
                ),
            ]
        )
    )

    assert (
            result.quick_hosts
            .top_hosts[0]
            .share
            == pytest.approx(
        2 / 3
    )
    )


def test_quick_research_host_summary():
    result = (
        aggregate_source_occurrences(
            [
                SourceOccurrence(
                    question_id="Q001",
                    mode="quick",
                    source_key="https://example.com/a",
                    domain="example.com",
                    title="A",
                    url="https://example.com/a",
                    rank=1,
                ),
                SourceOccurrence(
                    question_id="Q001",
                    mode="research",
                    source_key="https://example.com/b",
                    domain="example.com",
                    title="B",
                    url="https://example.com/b",
                    rank=1,
                ),
            ]
        )
    )

    assert (
            result.quick_hosts
            .total_occurrences
            == 1
    )

    assert (
            result.research_hosts
            .total_occurrences
            == 1
    )

    assert (
            result.all_hosts
            .top_hosts[0]
            .occurrence_count
            == 2
    )
