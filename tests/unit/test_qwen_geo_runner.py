from __future__ import annotations

import asyncio

import pytest

from app.qwen.analysis.geo_runner import (
    run_geo_analysis,
)
from app.qwen.analysis.models import (
    MentionBatchResult,
    MentionSummary,
    MentionTarget,
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


def _mention_result():
    return MentionBatchResult(
        summaries={
            "hongmao": (
                TargetMentionSummary(
                    target_id="hongmao",
                    quick=MentionSummary(
                        valid_count=1,
                        mentioned_count=1,
                        mention_rate=1.0,
                    ),
                    research=MentionSummary(
                        valid_count=1,
                        mentioned_count=1,
                        mention_rate=1.0,
                    ),
                    all_answers=MentionSummary(
                        valid_count=2,
                        mentioned_count=2,
                        mention_rate=1.0,
                    ),
                    question_level=MentionSummary(
                        valid_count=1,
                        mentioned_count=1,
                        mention_rate=1.0,
                    ),
                )
            )
        }
    )


def _sentiment_result():
    return SentimentBatchResult(
        summaries={
            "hongmao": (
                TargetSentimentSummary(
                    target_id="hongmao",
                    quick=SentimentSummary(
                        non_negative_rate=1.0,
                        negative_rate=0.0,
                    ),
                    research=SentimentSummary(
                        non_negative_rate=0.5,
                        negative_rate=0.5,
                    ),
                    all_answers=SentimentSummary(
                        non_negative_rate=0.75,
                        negative_rate=0.25,
                    ),
                    question_level=SentimentSummary(
                        non_negative_rate=0.5,
                        negative_rate=0.5,
                    ),
                )
            )
        }
    )


def _source_result():
    return SourceAnalysisResult(
        quick=SourceSummary(
            total_occurrences=10,
            unique_source_count=8,
            top10_share=1.0,
        ),
        research=SourceSummary(
            total_occurrences=20,
            unique_source_count=15,
            top10_share=0.8,
        ),
        all_sources=SourceSummary(
            total_occurrences=30,
            unique_source_count=20,
            top10_share=0.7,
        ),
        quick_hosts=HostSummary(
            total_occurrences=10,
            unique_host_count=6,
            top10_share=1.0,
        ),
        research_hosts=HostSummary(
            total_occurrences=20,
            unique_host_count=10,
            top10_share=1.0,
        ),
        all_hosts=HostSummary(
            total_occurrences=30,
            unique_host_count=12,
            top10_share=0.9,
        ),
    )


def test_run_geo_analysis(
    monkeypatch,
):
    calls = []

    def fake_mention(
        batch_dir,
        targets,
    ):
        calls.append(
            "mention"
        )

        assert len(targets) == 1

        return _mention_result()

    async def fake_sentiment(
        batch_dir,
        targets,
        classifier,
    ):
        calls.append(
            "sentiment"
        )

        assert len(targets) == 1

        return _sentiment_result()

    def fake_sources(
        batch_dir,
    ):
        calls.append(
            "sources"
        )

        return _source_result()

    monkeypatch.setattr(
        "app.qwen.analysis.geo_runner."
        "run_mention_analysis",
        fake_mention,
    )

    monkeypatch.setattr(
        "app.qwen.analysis.geo_runner."
        "run_sentiment_analysis",
        fake_sentiment,
    )

    monkeypatch.setattr(
        "app.qwen.analysis.geo_runner."
        "run_source_analysis",
        fake_sources,
    )

    result = asyncio.run(
        run_geo_analysis(
            "test-batch",
            [
                MentionTarget(
                    target_id="hongmao",
                    aliases=[
                        "鸿茅药酒",
                        "鸿茅",
                    ],
                )
            ],
            object(),
        )
    )

    assert calls == [
        "mention",
        "sentiment",
        "sources",
    ]

    assert (
        result.platform
        == "qwen"
    )

    assert (
        result.metrics
        .targets["hongmao"]
        .mention_rate.all
        == 1.0
    )

    assert (
        result.metrics
        .targets["hongmao"]
        .non_negative_rate.all
        == 0.75
    )

    assert (
        result.metrics
        .sources
        .source_occurrences.all
        == 30
    )


def test_run_geo_analysis_rejects_empty_targets():
    with pytest.raises(
        ValueError,
        match="at least one target",
    ):
        asyncio.run(
            run_geo_analysis(
                "test-batch",
                [],
                object(),
            )
        )


def test_run_geo_analysis_rejects_duplicate_targets():
    target = MentionTarget(
        target_id="hongmao",
        aliases=[
            "鸿茅"
        ],
    )

    with pytest.raises(
        ValueError,
        match="duplicate target_id",
    ):
        asyncio.run(
            run_geo_analysis(
                "test-batch",
                [
                    target,
                    target,
                ],
                object(),
            )
        )
