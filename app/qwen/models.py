from __future__ import annotations

from typing import Literal

from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
)


class QwenSource(BaseModel):
    rank: int
    title: str
    url: str


class QwenAnswerResult(BaseModel):
    platform: str = "qwen"

    question: str
    answer: str

    turn_id: str
    chat_url: str

    mode: str = "quick"
    mode_label: str = "快速"

    question_id: str | None = None

    search_queries: list[str] = Field(
        default_factory=list
    )

    sources: list[QwenSource] = Field(
        default_factory=list
    )

    # 当前千问 Web 最终正文没有暴露
    # sentence-level citation -> source 映射
    citation_mapping_available: bool = False

    acquired_at: datetime = Field(
        default_factory=datetime.now
    )


class QwenTaskRunResult(BaseModel):
    question_id: str
    mode: str
    question: str

    status: Literal[
        "pass",
        "fail",
        "blocked",
    ]

    output_path: str | None = None

    error_type: str | None = None
    error_message: str | None = None

class QwenBatchSummary(BaseModel):
    platform: str = "qwen"

    status: Literal[
        "completed",
        "partial",
        "blocked",
    ]

    planned_count: int
    executed_count: int

    pass_count: int
    fail_count: int
    blocked_count: int
    pending_count: int

    task_results: list[
        QwenTaskRunResult
    ] = Field(
        default_factory=list
    )

    started_at: datetime
    finished_at: datetime
