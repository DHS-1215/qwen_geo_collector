from __future__ import annotations

from pydantic import BaseModel, Field

from app.qwen.analysis.models import (
    MentionBatchResult,
)
from app.qwen.analysis.sentiment_models import (
    SentimentBatchResult,
)
from app.qwen.analysis.source_models import (
    SourceAnalysisResult,
)


class FourScopeRate(BaseModel):
    quick: float = 0.0
    research: float = 0.0
    all: float = 0.0
    question: float = 0.0


class ThreeScopeRate(BaseModel):
    quick: float = 0.0
    research: float = 0.0
    all: float = 0.0


class ThreeScopeCount(BaseModel):
    quick: int = 0
    research: int = 0
    all: int = 0


class GeoTargetMetrics(BaseModel):
    mention_rate: FourScopeRate = Field(
        default_factory=FourScopeRate
    )

    non_negative_rate: FourScopeRate = Field(
        default_factory=FourScopeRate
    )

    negative_rate: FourScopeRate = Field(
        default_factory=FourScopeRate
    )


class GeoSourceMetrics(BaseModel):
    source_top10_share: ThreeScopeRate = Field(
        default_factory=ThreeScopeRate
    )

    host_top10_share: ThreeScopeRate = Field(
        default_factory=ThreeScopeRate
    )

    source_occurrences: ThreeScopeCount = Field(
        default_factory=ThreeScopeCount
    )

    unique_sources: ThreeScopeCount = Field(
        default_factory=ThreeScopeCount
    )

    unique_hosts: ThreeScopeCount = Field(
        default_factory=ThreeScopeCount
    )


class GeoAnalysisMetrics(BaseModel):
    platform: str = "qwen"

    targets: dict[
        str,
        GeoTargetMetrics,
    ] = Field(
        default_factory=dict
    )

    sources: GeoSourceMetrics = Field(
        default_factory=GeoSourceMetrics
    )


class GeoAnalysisBundle(BaseModel):
    platform: str = "qwen"

    mention: MentionBatchResult
    sentiment: SentimentBatchResult
    sources: SourceAnalysisResult

    metrics: GeoAnalysisMetrics
