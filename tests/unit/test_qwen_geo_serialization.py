from __future__ import annotations

import json
from pathlib import Path

from app.qwen.analysis.geo_models import (
    FourScopeRate,
    GeoAnalysisBundle,
    GeoAnalysisMetrics,
    GeoSourceMetrics,
    GeoTargetMetrics,
    ThreeScopeCount,
    ThreeScopeRate,
)
from app.qwen.analysis.geo_serialization import (
    serialize_geo_analysis_metrics,
    serialize_geo_analysis_result,
    write_geo_analysis_metrics,
    write_geo_analysis_result,
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


def _metrics():
    return GeoAnalysisMetrics(
        targets={
            "hongmao": (
                GeoTargetMetrics(
                    mention_rate=FourScopeRate(
                        quick=1.0,
                        research=1.0,
                        all=1.0,
                        question=1.0,
                    ),
                    non_negative_rate=FourScopeRate(
                        quick=0.875,
                        research=0.625,
                        all=0.75,
                        question=0.625,
                    ),
                    negative_rate=FourScopeRate(
                        quick=0.125,
                        research=0.375,
                        all=0.25,
                        question=0.375,
                    ),
                )
            )
        },
        sources=GeoSourceMetrics(
            source_top10_share=ThreeScopeRate(
                quick=0.26,
                research=0.23,
                all=0.22,
            ),
            host_top10_share=ThreeScopeRate(
                quick=0.52,
                research=0.53,
                all=0.51,
            ),
            source_occurrences=ThreeScopeCount(
                quick=99,
                research=141,
                all=240,
            ),
            unique_sources=ThreeScopeCount(
                quick=81,
                research=111,
                all=152,
            ),
            unique_hosts=ThreeScopeCount(
                quick=53,
                research=66,
                all=88,
            ),
        ),
    )


def _bundle():
    metrics = _metrics()

    return GeoAnalysisBundle(
        mention=MentionBatchResult(),
        sentiment=SentimentBatchResult(),
        sources=SourceAnalysisResult(),
        metrics=metrics,
    )


def test_serialize_geo_analysis_metrics():
    payload = (
        serialize_geo_analysis_metrics(
            _metrics()
        )
    )

    assert (
        payload["platform"]
        == "qwen"
    )

    assert (
        payload["targets"]
        ["hongmao"]
        ["mention_rate"]
        ["all"]
        == 1.0
    )

    assert (
        payload["sources"]
        ["source_occurrences"]
        ["all"]
        == 240
    )


def test_serialize_geo_analysis_result():
    payload = (
        serialize_geo_analysis_result(
            _bundle()
        )
    )

    assert (
        payload["platform"]
        == "qwen"
    )

    assert "mention" in payload
    assert "sentiment" in payload
    assert "sources" in payload
    assert "metrics" in payload


def test_write_geo_analysis_files(
    tmp_path: Path,
):
    bundle = _bundle()

    result_path = (
        write_geo_analysis_result(
            bundle,
            tmp_path
            / "geo_analysis_result.json",
        )
    )

    metrics_path = (
        write_geo_analysis_metrics(
            bundle.metrics,
            tmp_path
            / "geo_analysis_metrics.json",
        )
    )

    assert result_path.exists()
    assert metrics_path.exists()

    result_data = json.loads(
        result_path.read_text(
            encoding="utf-8"
        )
    )

    metrics_data = json.loads(
        metrics_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        result_data["platform"]
        == "qwen"
    )

    assert (
        metrics_data["targets"]
        ["hongmao"]
        ["non_negative_rate"]
        ["all"]
        == 0.75
    )
