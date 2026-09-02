from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SentimentLabel = Literal[
    "positive",
    "neutral",
    "negative",
]

SentimentStatus = Literal[
    "success",
    "success_with_warnings",
    "failed",
    "rate_limited",
    "timeout",
    "not_applicable",
]


class SentimentResult(BaseModel):
    question_id: str
    mode: str

    target_id: str

    classification_planned: bool

    sentiment_status: SentimentStatus

    model_sentiment: (
        SentimentLabel | None
    ) = None

    final_sentiment: (
        SentimentLabel | None
    ) = None

    provider: str | None = None

    reason: str | None = None

    evidence: list[str] = Field(
        default_factory=list
    )

    confidence: float | None = None

    rule_hit: bool = False
    rule_override: bool = False

    warnings: list[str] = Field(
        default_factory=list
    )

    error_type: str | None = None
    error_message: str | None = None


class SentimentSummary(BaseModel):
    planned_mention_count: int = 0

    classified_mention_count: int = 0

    classification_failed_count: int = 0

    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0

    non_negative_count: int = 0

    positive_rate: float = 0.0
    neutral_rate: float = 0.0
    negative_rate: float = 0.0

    non_negative_rate: float = 0.0


class TargetSentimentSummary(BaseModel):
    target_id: str

    quick: SentimentSummary

    research: SentimentSummary

    all_answers: SentimentSummary

    question_level: SentimentSummary


class SentimentBatchResult(BaseModel):
    details: list[
        SentimentResult
    ] = Field(
        default_factory=list
    )

    summaries: dict[
        str,
        TargetSentimentSummary,
    ] = Field(
        default_factory=dict
    )
