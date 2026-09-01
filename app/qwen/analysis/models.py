from __future__ import annotations

from pydantic import BaseModel, Field


class MentionTarget(BaseModel):
    target_id: str
    aliases: list[str]


class MentionResult(BaseModel):
    target_id: str
    mention_count: int
    mentioned: bool


class MentionDetail(BaseModel):
    question_id: str
    mode: str
    target_id: str
    mention_count: int
    mentioned: bool


class MentionSummary(BaseModel):
    valid_count: int
    mentioned_count: int
    mention_rate: float


class TargetMentionSummary(BaseModel):
    target_id: str
    quick: MentionSummary
    research: MentionSummary
    all_answers: MentionSummary
    question_level: MentionSummary


class MentionBatchResult(BaseModel):
    details: list[MentionDetail] = Field(
        default_factory=list
    )
    summaries: dict[
        str,
        TargetMentionSummary,
    ] = Field(
        default_factory=dict
    )
