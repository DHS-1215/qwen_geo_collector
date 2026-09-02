from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.qwen.pipeline.models import (
    QwenPipelineResult,
)


def test_pipeline_completed_result() -> None:
    started_at = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    finished_at = datetime(
        2026,
        8,
        28,
        16,
        10,
    )

    result = QwenPipelineResult(
        status="completed",
        batch_dir=Path(
            "output/run_001"
        ),
        package_path=Path(
            "output/"
            "geo_package_qwen_run_001.zip"
        ),
        planned_count=2,
        pass_count=2,
        fail_count=0,
        blocked_count=0,
        pending_count=0,
        package_verified=True,
        started_at=started_at,
        finished_at=finished_at,
    )

    assert (
            result.status
            == "completed"
    )

    assert (
            result.package_verified
            is True
    )

    assert (
            result.package_path
            == Path(
        "output/"
        "geo_package_qwen_run_001.zip"
    )
    )

    assert (
            result.pending_count
            == 0
    )


def test_pipeline_partial_result() -> None:
    result = QwenPipelineResult(
        status="partial",
        batch_dir=Path(
            "output/run_002"
        ),
        package_path=Path(
            "output/"
            "geo_package_qwen_run_002.zip"
        ),
        planned_count=3,
        pass_count=2,
        fail_count=1,
        blocked_count=0,
        pending_count=0,
        package_verified=True,
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
            15,
        ),
    )

    assert (
            result.status
            == "partial"
    )

    assert (
            result.fail_count
            == 1
    )

    assert (
            result.package_verified
            is True
    )


def test_pipeline_blocked_result() -> None:
    result = QwenPipelineResult(
        status="blocked",
        batch_dir=Path(
            "output/run_003"
        ),
        package_path=None,
        planned_count=3,
        pass_count=1,
        fail_count=0,
        blocked_count=1,
        pending_count=1,
        package_verified=False,
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
            5,
        ),
    )

    assert (
            result.status
            == "blocked"
    )

    assert (
            result.package_path
            is None
    )

    assert (
            result.blocked_count
            == 1
    )

    assert (
            result.pending_count
            == 1
    )

    assert (
            result.package_verified
            is False
    )


def test_pipeline_failed_result() -> None:
    result = QwenPipelineResult(
        status="failed",
        batch_dir=Path(
            "output/run_004"
        ),
        package_path=None,
        planned_count=2,
        pass_count=2,
        fail_count=0,
        blocked_count=0,
        pending_count=0,
        package_verified=False,
        error_type="ValueError",
        error_message="模拟验包失败",
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
            8,
        ),
    )

    assert (
            result.status
            == "failed"
    )

    assert (
            result.package_path
            is None
    )

    assert (
            result.error_type
            == "ValueError"
    )

    assert (
            result.error_message
            == "模拟验包失败"
    )
