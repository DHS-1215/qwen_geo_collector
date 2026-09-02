from __future__ import annotations

import pytest

from app.qwen.analysis.geo_metrics import (
    build_geo_metrics,
)
from app.qwen.analysis.models import (
    MentionBatchResult,
    MentionSummary,
    TargetMentionSummary,
)
from app.qwen.analysis.sentiment_models import (
    SentimentBatchResult,
    SentimentSummary,
    TargetSentimentSummary,
)
from app.qwen.analysis.source_models import (
    HostSummary,
    SourceAnalysisResult,
    SourceSummary,
)


def _mention(
    target_id: str = "hongmao",
) -> MentionBatchResult:
    return MentionBatchResult(
        summaries={
            target_id: (
                TargetMentionSummary(
                    target_id=target_id,
                    quick=MentionSummary(
                        valid_count=8,
                        mentioned_count=8,
                        mention_rate=1.0,
                    ),
                    research=MentionSummary(
                        valid_count=8,
                        mentioned_count=8,
                        mention_rate=1.0,
                    ),
                    all_answers=MentionSummary(
                        valid_count=16,
                        mentioned_count=16,
                        mention_rate=1.0,
                    ),
                    question_level=MentionSummary(
                        valid_count=8,
                        mentioned_count=8,
                        mention_rate=1.0,
                    ),
                )
            )
        }
    )


def _sentiment(
    target_id: str = "hongmao",
) -> SentimentBatchResult:
    return SentimentBatchResult(
        summaries={
            target_id: (
                TargetSentimentSummary(
                    target_id=target_id,
                    quick=SentimentSummary(
                        non_negative_rate=0.875,
                        negative_rate=0.125,
                    ),
                    research=SentimentSummary(
                        non_negative_rate=0.625,
                        negative_rate=0.375,
                    ),
                    all_answers=SentimentSummary(
                        non_negative_rate=0.75,
                        negative_rate=0.25,
                    ),
                    question_level=SentimentSummary(
                        non_negative_rate=0.625,
                        negative_rate=0.375,
                    ),
                )
            )
        }
    )


def _sources() -> SourceAnalysisResult:
    return SourceAnalysisResult(
        quick=SourceSummary(
            total_occurrences=99,
            unique_source_count=81,
            top10_share=(
                26 / 99
            ),
        ),
        research=SourceSummary(
            total_occurrences=141,
            unique_source_count=111,
            top10_share=(
                33 / 141
            ),
        ),
        all_sources=SourceSummary(
            total_occurrences=240,
            unique_source_count=152,
            top10_share=(
                53 / 240
            ),
        ),
        quick_hosts=HostSummary(
            total_occurrences=99,
            unique_host_count=53,
            top10_share=(
                52 / 99
            ),
        ),
        research_hosts=HostSummary(
            total_occurrences=141,
            unique_host_count=66,
            top10_share=(
                75 / 141
            ),
        ),
        all_hosts=HostSummary(
            total_occurrences=240,
            unique_host_count=88,
            top10_share=(
                122 / 240
            ),
        ),
    )


def test_build_target_geo_metrics():
    result = build_geo_metrics(
        mention=_mention(),
        sentiment=_sentiment(),
        sources=_sources(),
    )

    target = result.targets[
        "hongmao"
    ]

    assert (
        target.mention_rate.quick
        == 1.0
    )

    assert (
        target.non_negative_rate.quick
        == 0.875
    )

    assert (
        target.non_negative_rate.research
        == 0.625
    )

    assert (
        target.negative_rate.all
        == 0.25
    )


def test_build_source_geo_metrics():
    result = build_geo_metrics(
        mention=_mention(),
        sentiment=_sentiment(),
        sources=_sources(),
    )

    assert (
        result.sources
        .source_occurrences.all
        == 240
    )

    assert (
        result.sources
        .unique_sources.all
        == 152
    )

    assert (
        result.sources
        .unique_hosts.all
        == 88
    )

    assert (
        result.sources
        .source_top10_share.all
        == pytest.approx(
            53 / 240
        )
    )

    assert (
        result.sources
        .host_top10_share.all
        == pytest.approx(
            122 / 240
        )
    )


def test_target_mismatch_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "target sets do not match"
        ),
    ):
        build_geo_metrics(
            mention=_mention(
                "hongmao"
            ),
            sentiment=_sentiment(
                "other"
            ),
            sources=_sources(),
        )
