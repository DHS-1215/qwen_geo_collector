from __future__ import annotations

from app.qwen.analysis.geo_models import (
    FourScopeRate,
    GeoAnalysisMetrics,
    GeoSourceMetrics,
    GeoTargetMetrics,
    ThreeScopeCount,
    ThreeScopeRate,
)
from app.qwen.analysis.models import (
    MentionBatchResult,
)
from app.qwen.analysis.sentiment_models import (
    SentimentBatchResult,
)
from app.qwen.analysis.source_models import (
    SourceAnalysisResult,
)


def build_geo_metrics(
    *,
    mention: MentionBatchResult,
    sentiment: SentimentBatchResult,
    sources: SourceAnalysisResult,
) -> GeoAnalysisMetrics:
    mention_targets = set(
        mention.summaries
    )

    sentiment_targets = set(
        sentiment.summaries
    )

    if (
        mention_targets
        != sentiment_targets
    ):
        raise ValueError(
            "mention and sentiment "
            "target sets do not match"
        )

    targets: dict[
        str,
        GeoTargetMetrics,
    ] = {}

    for target_id in sorted(
        mention_targets
    ):
        mention_summary = (
            mention.summaries[
                target_id
            ]
        )

        sentiment_summary = (
            sentiment.summaries[
                target_id
            ]
        )

        targets[target_id] = (
            GeoTargetMetrics(
                mention_rate=FourScopeRate(
                    quick=(
                        mention_summary.quick
                        .mention_rate
                    ),
                    research=(
                        mention_summary.research
                        .mention_rate
                    ),
                    all=(
                        mention_summary.all_answers
                        .mention_rate
                    ),
                    question=(
                        mention_summary.question_level
                        .mention_rate
                    ),
                ),
                non_negative_rate=(
                    FourScopeRate(
                        quick=(
                            sentiment_summary.quick
                            .non_negative_rate
                        ),
                        research=(
                            sentiment_summary.research
                            .non_negative_rate
                        ),
                        all=(
                            sentiment_summary.all_answers
                            .non_negative_rate
                        ),
                        question=(
                            sentiment_summary.question_level
                            .non_negative_rate
                        ),
                    )
                ),
                negative_rate=(
                    FourScopeRate(
                        quick=(
                            sentiment_summary.quick
                            .negative_rate
                        ),
                        research=(
                            sentiment_summary.research
                            .negative_rate
                        ),
                        all=(
                            sentiment_summary.all_answers
                            .negative_rate
                        ),
                        question=(
                            sentiment_summary.question_level
                            .negative_rate
                        ),
                    )
                ),
            )
        )

    source_metrics = GeoSourceMetrics(
        source_top10_share=ThreeScopeRate(
            quick=(
                sources.quick
                .top10_share
            ),
            research=(
                sources.research
                .top10_share
            ),
            all=(
                sources.all_sources
                .top10_share
            ),
        ),
        host_top10_share=ThreeScopeRate(
            quick=(
                sources.quick_hosts
                .top10_share
            ),
            research=(
                sources.research_hosts
                .top10_share
            ),
            all=(
                sources.all_hosts
                .top10_share
            ),
        ),
        source_occurrences=ThreeScopeCount(
            quick=(
                sources.quick
                .total_occurrences
            ),
            research=(
                sources.research
                .total_occurrences
            ),
            all=(
                sources.all_sources
                .total_occurrences
            ),
        ),
        unique_sources=ThreeScopeCount(
            quick=(
                sources.quick
                .unique_source_count
            ),
            research=(
                sources.research
                .unique_source_count
            ),
            all=(
                sources.all_sources
                .unique_source_count
            ),
        ),
        unique_hosts=ThreeScopeCount(
            quick=(
                sources.quick_hosts
                .unique_host_count
            ),
            research=(
                sources.research_hosts
                .unique_host_count
            ),
            all=(
                sources.all_hosts
                .unique_host_count
            ),
        ),
    )

    return GeoAnalysisMetrics(
        targets=targets,
        sources=source_metrics,
    )
