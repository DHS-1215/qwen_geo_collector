from __future__ import annotations
import pytest

from app.qwen.models import QwenBatchSummary

from datetime import datetime

from pathlib import Path
from unittest.mock import Mock

from app.qwen.pipeline import runner as pipeline_runner_module
from app.qwen.pipeline.runner import QwenPipelineRunner
from app.qwen.tasks import QwenTask


def test_run_batch_phase_runs_tasks_and_loads_summary(
        tmp_path: Path,
        monkeypatch,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = tmp_path

    expected_summary = Mock()

    load_summary = Mock(
        return_value=expected_summary
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "load_batch_summary",
        load_summary,
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    tasks = [
        QwenTask(
            question_id="Q001",
            question="鸿茅药酒到底是药还是酒？",
            mode="quick",
        ),
    ]

    result = pipeline.run_batch_phase(
        tasks,
    )

    batch_runner.run.assert_called_once_with(
        tasks,
        resume=False,
    )

    load_summary.assert_called_once_with(
        tmp_path
    )

    assert result is expected_summary


def test_run_batch_phase_passes_resume_true(
        tmp_path: Path,
        monkeypatch,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = tmp_path

    expected_summary = Mock()

    load_summary = Mock(
        return_value=expected_summary
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "load_batch_summary",
        load_summary,
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    tasks = [
        QwenTask(
            question_id="Q001",
            question="鸿茅药酒到底是药还是酒？",
            mode="research",
        ),
    ]

    result = pipeline.run_batch_phase(
        tasks,
        resume=True,
    )

    batch_runner.run.assert_called_once_with(
        tasks,
        resume=True,
    )

    load_summary.assert_called_once_with(
        tmp_path
    )

    assert result is expected_summary


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
        status = "blocked"
    elif fail_count > 0:
        status = "partial"
    else:
        status = "completed"

    return QwenBatchSummary(
        platform="qwen",
        status=status,
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


def test_run_package_phase_exports_and_verifies(
        tmp_path: Path,
        monkeypatch,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = tmp_path / "batch"

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    export_package = Mock()
    verify_package = Mock()

    monkeypatch.setattr(
        pipeline_runner_module,
        "export_package_zip",
        export_package,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_package_zip",
        verify_package,
    )

    summary = build_summary(
        pass_count=2,
    )

    package_path = (
            tmp_path
            / "geo_package_qwen_test.zip"
    )

    result = pipeline.run_package_phase(
        summary,
        package_path=package_path,
        package_id="qwen-test",
    )

    export_package.assert_called_once_with(
        batch_dir=tmp_path / "batch",
        output_zip=package_path,
        package_id="qwen-test",
    )

    verify_package.assert_called_once_with(
        package_path
    )

    assert result == package_path


def test_run_package_phase_allows_partial_batch(
        tmp_path: Path,
        monkeypatch,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = tmp_path / "batch"

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    export_package = Mock()
    verify_package = Mock()

    monkeypatch.setattr(
        pipeline_runner_module,
        "export_package_zip",
        export_package,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_package_zip",
        verify_package,
    )

    summary = build_summary(
        pass_count=2,
        fail_count=1,
    )

    package_path = (
            tmp_path
            / "partial.zip"
    )

    result = pipeline.run_package_phase(
        summary,
        package_path=package_path,
        package_id="qwen-partial",
    )

    assert result == package_path

    export_package.assert_called_once()
    verify_package.assert_called_once()


def test_run_package_phase_rejects_blocked_batch(
        tmp_path: Path,
        monkeypatch,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = tmp_path / "batch"

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    export_package = Mock()
    verify_package = Mock()

    monkeypatch.setattr(
        pipeline_runner_module,
        "export_package_zip",
        export_package,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_package_zip",
        verify_package,
    )

    summary = build_summary(
        pass_count=1,
        blocked_count=1,
        pending_count=2,
    )

    with pytest.raises(
            ValueError,
            match="resume collection",
    ):
        pipeline.run_package_phase(
            summary,
            package_path=(
                    tmp_path / "blocked.zip"
            ),
            package_id="qwen-blocked",
        )

    export_package.assert_not_called()
    verify_package.assert_not_called()


def test_run_returns_completed_result(
        tmp_path: Path,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = (
            tmp_path / "batch"
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    summary = build_summary(
        pass_count=2,
    )

    package_path = (
            tmp_path / "completed.zip"
    )

    pipeline.run_batch_phase = Mock(
        return_value=summary
    )

    pipeline.run_package_phase = Mock(
        return_value=package_path
    )

    tasks = [
        QwenTask(
            question_id="Q001",
            question="问题1",
            mode="quick",
        ),
        QwenTask(
            question_id="Q002",
            question="问题2",
            mode="research",
        ),
    ]

    result = pipeline.run(
        tasks,
        package_path=package_path,
        package_id="qwen-completed",
    )

    assert result.status == "completed"
    assert result.package_verified is True
    assert result.package_path == package_path

    assert result.planned_count == 2
    assert result.pass_count == 2
    assert result.fail_count == 0
    assert result.blocked_count == 0
    assert result.pending_count == 0

    pipeline.run_batch_phase.assert_called_once_with(
        tasks,
        resume=False,
    )

    pipeline.run_package_phase.assert_called_once_with(
        summary,
        package_path=package_path,
        package_id="qwen-completed",
    )


def test_run_returns_partial_result(
        tmp_path: Path,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = (
            tmp_path / "batch"
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    summary = build_summary(
        pass_count=2,
        fail_count=1,
    )

    package_path = (
            tmp_path / "partial.zip"
    )

    pipeline.run_batch_phase = Mock(
        return_value=summary
    )

    pipeline.run_package_phase = Mock(
        return_value=package_path
    )

    tasks = [
        QwenTask(
            question_id="Q001",
            question="问题1",
            mode="quick",
        ),
    ]

    result = pipeline.run(
        tasks,
        package_path=package_path,
        package_id="qwen-partial",
    )

    assert result.status == "partial"
    assert result.package_verified is True
    assert result.pass_count == 2
    assert result.fail_count == 1


def test_run_returns_blocked_without_export(
        tmp_path: Path,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = (
            tmp_path / "batch"
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    summary = build_summary(
        pass_count=1,
        blocked_count=1,
        pending_count=2,
    )

    pipeline.run_batch_phase = Mock(
        return_value=summary
    )

    pipeline.run_package_phase = Mock()

    tasks = [
        QwenTask(
            question_id="Q001",
            question="问题1",
            mode="quick",
        ),
    ]

    result = pipeline.run(
        tasks,
        package_path=(
                tmp_path / "blocked.zip"
        ),
        package_id="qwen-blocked",
    )

    assert result.status == "blocked"
    assert result.package_path is None
    assert result.package_verified is False

    assert result.blocked_count == 1
    assert result.pending_count == 2

    pipeline.run_package_phase.assert_not_called()


def test_run_returns_failed_when_package_phase_fails(
        tmp_path: Path,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = (
            tmp_path / "batch"
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    summary = build_summary(
        pass_count=2,
    )

    pipeline.run_batch_phase = Mock(
        return_value=summary
    )

    pipeline.run_package_phase = Mock(
        side_effect=ValueError(
            "模拟验包失败"
        )
    )

    tasks = [
        QwenTask(
            question_id="Q001",
            question="问题1",
            mode="quick",
        ),
    ]

    result = pipeline.run(
        tasks,
        package_path=(
                tmp_path / "failed.zip"
        ),
        package_id="qwen-failed",
    )

    assert result.status == "failed"
    assert result.package_verified is False
    assert result.package_path is None

    assert (
            result.error_type
            == "ValueError"
    )

    assert (
            result.error_message
            == "模拟验包失败"
    )

    assert result.pass_count == 2
