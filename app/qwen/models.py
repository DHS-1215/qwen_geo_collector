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


class QwenSourceQuality(BaseModel):
    # unknown is used for historical results without diagnostics.
    status: Literal[
        "unknown",
        "success",
        "partial_success",
        "links_unavailable",
        "panel_unavailable",
        "unreadable_cards",
        "extraction_incomplete",
        "no_visible_source_entry",
    ] = "unknown"

    source_entry_detected: bool = False
    source_card_count: int = Field(default=0, ge=0)
    valid_source_count: int = Field(default=0, ge=0)
    invalid_url_count: int = Field(default=0, ge=0)
    unreadable_card_count: int = Field(default=0, ge=0)
    workflow_link_count: int = Field(default=0, ge=0)


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

    source_quality: QwenSourceQuality = Field(
        default_factory=QwenSourceQuality
    )

    screenshot_path: str | None = None
    screenshot_sha256: str | None = None
    screenshot_size_bytes: int | None = None
    screenshot_width: int | None = None
    screenshot_height: int | None = None


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
