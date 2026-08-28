from __future__ import annotations

import json
from pathlib import Path

from app.qwen.models import (
    QwenAnswerResult,
    QwenBatchSummary,
)


def load_batch_summary(
        batch_dir: str | Path,
) -> QwenBatchSummary:
    batch_dir = Path(
        batch_dir
    )

    summary_path = (
            batch_dir
            / "batch_summary.json"
    )

    if not summary_path.exists():
        raise FileNotFoundError(
            f"batch summary not found: "
            f"{summary_path}"
        )

    try:
        data = json.loads(
            summary_path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid batch summary JSON: "
            f"{summary_path}"
        ) from exc

    return QwenBatchSummary(
        **data
    )


def load_answer_result(
        answer_path: str | Path,
) -> QwenAnswerResult:
    answer_path = Path(
        answer_path
    )

    if not answer_path.exists():
        raise FileNotFoundError(
            f"answer result not found: "
            f"{answer_path}"
        )

    try:
        data = json.loads(
            answer_path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid answer result JSON: "
            f"{answer_path}"
        ) from exc

    return QwenAnswerResult(
        **data
    )
