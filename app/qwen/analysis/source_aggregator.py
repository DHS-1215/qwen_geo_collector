from __future__ import annotations

from collections import defaultdict

from app.qwen.analysis.source_models import (
    HostRankItem,
    HostSummary,
    SourceAnalysisResult,
    SourceOccurrence,
    SourceRankItem,
    SourceSummary,
)

TOP_SOURCE_LIMIT = 10


def _deduplicate_occurrences(
        occurrences: list[SourceOccurrence],
) -> list[SourceOccurrence]:
    """
    同一回答内，同一个 canonical source 只算一次。

    回答身份：
    question_id + mode
    """
    seen: set[
        tuple[str, str, str]
    ] = set()

    result: list[
        SourceOccurrence
    ] = []

    for item in occurrences:
        key = (
            item.question_id,
            item.mode,
            item.source_key,
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


def _build_summary(
        occurrences: list[SourceOccurrence],
) -> SourceSummary:
    if not occurrences:
        return SourceSummary()

    grouped: dict[
        str,
        list[
            tuple[
                int,
                SourceOccurrence,
            ]
        ],
    ] = defaultdict(list)

    for seen_order, item in enumerate(
            occurrences,
            start=1,
    ):
        grouped[
            item.source_key
        ].append(
            (
                seen_order,
                item,
            )
        )

    total_occurrences = len(
        occurrences
    )

    rank_items: list[
        SourceRankItem
    ] = []

    for (
            source_key,
            source_occurrences,
    ) in grouped.items():
        first_seen_order = min(
            seen_order
            for (
                seen_order,
                _,
            ) in source_occurrences
        )

        items = [
            item
            for (
                _,
                item,
            ) in source_occurrences
        ]

        first_item = (
            source_occurrences[0][1]
        )

        occurrence_count = len(
            items
        )

        question_count = len(
            {
                item.question_id
                for item in items
            }
        )

        average_order = (
                sum(
                    item.rank
                    for item in items
                )
                / occurrence_count
        )

        share = (
                occurrence_count
                / total_occurrences
        )

        rank_items.append(
            SourceRankItem(
                source_key=source_key,
                domain=(
                    first_item.domain
                ),
                title=(
                    first_item.title
                ),
                url=(
                    first_item.url
                ),
                occurrence_count=(
                    occurrence_count
                ),
                question_count=(
                    question_count
                ),
                average_order=(
                    average_order
                ),
                first_seen_order=(
                    first_seen_order
                ),
                share=share,
            )
        )

    rank_items.sort(
        key=lambda item: (
            -item.occurrence_count,
            -item.question_count,
            item.average_order,
            item.first_seen_order,
            item.source_key,
        )
    )

    top_sources = rank_items[
                  :TOP_SOURCE_LIMIT
                  ]

    top10_occurrences = sum(
        item.occurrence_count
        for item in top_sources
    )

    top10_share = (
            top10_occurrences
            / total_occurrences
    )

    return SourceSummary(
        total_occurrences=(
            total_occurrences
        ),
        unique_source_count=len(
            rank_items
        ),
        top10_occurrences=(
            top10_occurrences
        ),
        top10_share=(
            top10_share
        ),
        top_sources=(
            top_sources
        ),
    )


def aggregate_source_occurrences(
        occurrences: list[SourceOccurrence],
) -> SourceAnalysisResult:
    deduplicated = (
        _deduplicate_occurrences(
            occurrences
        )
    )

    quick = [
        item
        for item in deduplicated
        if item.mode == "quick"
    ]

    research = [
        item
        for item in deduplicated
        if item.mode == "research"
    ]

    return SourceAnalysisResult(
        occurrences=deduplicated,

        quick=_build_summary(
            quick
        ),
        research=_build_summary(
            research
        ),
        all_sources=_build_summary(
            deduplicated
        ),

        quick_hosts=_build_host_summary(
            quick
        ),
        research_hosts=_build_host_summary(
            research
        ),
        all_hosts=_build_host_summary(
            deduplicated
        ),
    )


def _build_host_summary(
        occurrences: list[SourceOccurrence],
) -> HostSummary:
    if not occurrences:
        return HostSummary()

    grouped: dict[
        str,
        list[SourceOccurrence],
    ] = defaultdict(list)

    for item in occurrences:
        if not item.domain:
            continue

        grouped[
            item.domain
        ].append(item)

    total_occurrences = len(
        occurrences
    )

    items: list[
        HostRankItem
    ] = []

    for (
            host,
            host_occurrences,
    ) in grouped.items():
        occurrence_count = len(
            host_occurrences
        )

        question_count = len(
            {
                item.question_id
                for item
                in host_occurrences
            }
        )

        items.append(
            HostRankItem(
                host=host,
                occurrence_count=(
                    occurrence_count
                ),
                question_count=(
                    question_count
                ),
                share=(
                        occurrence_count
                        / total_occurrences
                ),
            )
        )

    items.sort(
        key=lambda item: (
            -item.occurrence_count,
            -item.question_count,
            item.host,
        )
    )

    top_hosts = items[
                :TOP_SOURCE_LIMIT
                ]

    top10_occurrences = sum(
        item.occurrence_count
        for item in top_hosts
    )

    return HostSummary(
        total_occurrences=(
            total_occurrences
        ),
        unique_host_count=len(
            items
        ),
        top10_occurrences=(
            top10_occurrences
        ),
        top10_share=(
                top10_occurrences
                / total_occurrences
        ),
        top_hosts=top_hosts,
    )
