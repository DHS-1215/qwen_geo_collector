from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


class QwenPackageManifest(BaseModel):
    schema_version: str = "geo_batch_v1"
    platform: str = "qwen"

    package_id: str
    created_at: datetime

    task_count: int
    answer_count: int
    source_count: int

    files: list[str] = Field(
        default_factory=list
    )


class QwenPackageTask(BaseModel):
    question_id: str
    question: str

    mode: Literal[
        "quick",
        "research",
    ]

    status: Literal[
        "pass",
        "fail",
        "blocked",
        "pending",
    ]

    error_type: str | None = None
    error_message: str | None = None


class QwenPackageAnswer(BaseModel):
    question_id: str
    question: str

    mode: Literal[
        "quick",
        "research",
    ]

    mode_label: str

    answer: str
    turn_id: str
    chat_url: str

    search_queries: list[str] = Field(
        default_factory=list
    )

    citation_mapping_available: bool = False

    acquired_at: datetime


class QwenPackageSource(BaseModel):
    occurrence_id: str

    question_id: str

    mode: Literal[
        "quick",
        "research",
    ]

    rank: int
    title: str
    url: str