from __future__ import annotations

from pydantic import BaseModel, Field


class SourceOccurrence(BaseModel):
    question_id: str
    mode: str

    source_key: str
    domain: str

    title: str
    url: str
    rank: int


class SourceRankItem(BaseModel):
    source_key: str
    domain: str

    title: str
    url: str

    occurrence_count: int
    question_count: int

    average_order: float
    first_seen_order: int

    share: float = 0.0


class SourceSummary(BaseModel):
    total_occurrences: int = 0
    unique_source_count: int = 0

    top10_occurrences: int = 0
    top10_share: float = 0.0

    top_sources: list[
        SourceRankItem
    ] = Field(
        default_factory=list
    )


class HostRankItem(BaseModel):
    host: str

    occurrence_count: int
    question_count: int

    share: float = 0.0


class HostSummary(BaseModel):
    total_occurrences: int = 0
    unique_host_count: int = 0

    top10_occurrences: int = 0
    top10_share: float = 0.0

    top_hosts: list[
        HostRankItem
    ] = Field(
        default_factory=list
    )


class SourceAnalysisResult(BaseModel):
    occurrences: list[
        SourceOccurrence
    ] = Field(
        default_factory=list
    )

    quick: SourceSummary = Field(
        default_factory=SourceSummary
    )

    research: SourceSummary = Field(
        default_factory=SourceSummary
    )

    all_sources: SourceSummary = Field(
        default_factory=SourceSummary
    )

    quick_hosts: HostSummary = Field(
        default_factory=HostSummary
    )

    research_hosts: HostSummary = Field(
        default_factory=HostSummary
    )

    all_hosts: HostSummary = Field(
        default_factory=HostSummary
    )
