from __future__ import annotations

from datetime import datetime

from app.qwen.models import QwenBatchSummary
from app.qwen.pipeline.gates import (
    can_export_package,
    resolve_post_batch_status,
)


def build_summary(
        *,
        pass_count: int = 0,
        fail_count: int = 0,
        blocked_count: int = 0,
        pending_count: int = 0,
) -> QwenBatchSummary:
    planned_count = (
            pass_count
            + fail_count
            + blocked_count
            + pending_count
    )

    executed_count = (
            pass_count
            + fail_count
            + blocked_count
    )

    if blocked_count > 0:
        batch_status = "blocked"
    elif fail_count > 0:
        batch_status = "partial"
    else:
        batch_status = "completed"

    return QwenBatchSummary(
        platform="qwen",
        status=batch_status,
        planned_count=planned_count,
        executed_count=executed_count,
        pass_count=pass_count,
        fail_count=fail_count,
        blocked_count=blocked_count,
        pending_count=pending_count,
        task_results=[],
        started_at=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        finished_at=datetime(
            2026,
            8,
            28,
            16,
            10,
        ),
    )


def test_completed_batch_can_export() -> None:
    summary = build_summary(
        pass_count=3,
    )

    assert (
            resolve_post_batch_status(summary)
            == "completed"
    )

    assert can_export_package(summary) is True


def test_partial_batch_cannot_export() -> None:
    summary = build_summary(
        pass_count=2,
        fail_count=1,
    )

    assert (
            resolve_post_batch_status(summary)
            == "partial"
    )

    assert can_export_package(summary) is False


def test_blocked_batch_cannot_export() -> None:
    summary = build_summary(
        pass_count=1,
        blocked_count=1,
        pending_count=1,
    )

    assert (
            resolve_post_batch_status(summary)
            == "blocked"
    )

    assert can_export_package(summary) is False


def test_pending_batch_cannot_export() -> None:
    summary = build_summary(
        pass_count=1,
        pending_count=2,
    )

    assert (
            resolve_post_batch_status(summary)
            == "blocked"
    )

    assert can_export_package(summary) is False
