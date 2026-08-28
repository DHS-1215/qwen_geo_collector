from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class QwenPipelineResult(BaseModel):
    status: Literal[
        "completed",
        "partial",
        "blocked",
        "failed",
    ]

    batch_dir: Path
    package_path: Path | None = None

    planned_count: int
    pass_count: int
    fail_count: int
    blocked_count: int
    pending_count: int

    package_verified: bool = False

    error_type: str | None = None
    error_message: str | None = None

    started_at: datetime
    finished_at: datetime