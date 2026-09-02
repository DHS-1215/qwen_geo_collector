from __future__ import annotations
import pytest

from app.qwen.models import QwenBatchSummary

from datetime import datetime

from pathlib import Path
from unittest.mock import Mock

from app.qwen.pipeline import runner as pipeline_runner_module
from app.qwen.pipeline.runner import QwenPipelineRunner
from app.qwen.tasks import QwenTask

from app.qwen.pipeline.models import (
    QwenPipelineResult,
)


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
        "export_central_package_zip",
        export_package,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_central_package_zip",
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
        batch_id="qwen-test",
        product_id="hongmao",
        product_name="????",
    )

    export_package.assert_called_once_with(
        batch_dir=tmp_path / "batch",
        output_zip=package_path,
        batch_id="qwen-test",
        product_id="hongmao",
        product_name="????",
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
        "export_central_package_zip",
        export_package,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_central_package_zip",
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
        batch_id="qwen-partial",
        product_id="hongmao",
        product_name="????",
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
        "export_central_package_zip",
        export_package,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_central_package_zip",
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
            batch_id="qwen-blocked",
            product_id="hongmao",
            product_name="????",
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
        batch_id="qwen-completed",
        product_id="hongmao",
        product_name="????",
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
        batch_id="qwen-completed",
        product_id="hongmao",
        product_name="????",
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
        batch_id="qwen-partial",
        product_id="hongmao",
        product_name="????",
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
        batch_id="qwen-blocked",
        product_id="hongmao",
        product_name="????",
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
        batch_id="qwen-failed",
        product_id="hongmao",
        product_name="????",
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


def test_finalize_result_writes_pipeline_result(
        tmp_path: Path,
        monkeypatch,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = (
            tmp_path / "batch"
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
    )

    write_result = Mock()

    monkeypatch.setattr(
        pipeline_runner_module,
        "write_pipeline_result",
        write_result,
    )

    result = QwenPipelineResult(
        status="completed",
        batch_dir=tmp_path / "batch",
        package_path=tmp_path / "package.zip",
        planned_count=2,
        pass_count=2,
        fail_count=0,
        blocked_count=0,
        pending_count=0,
        package_verified=True,
        started_at=datetime(
            2026,
            8,
            31,
            9,
            0,
        ),
        finished_at=datetime(
            2026,
            8,
            31,
            9,
            10,
        ),
    )

    returned = pipeline._finalize_result(
        result
    )

    write_result.assert_called_once_with(
        result,
        (
                tmp_path
                / "batch"
                / "pipeline_result.json"
        ),
    )

    assert returned is result


def test_analysis_configuration_must_be_complete(
        tmp_path: Path,
) -> None:
    batch_runner = Mock()
    batch_runner.output_dir = tmp_path

    with pytest.raises(
            ValueError,
            match="cannot be empty",
    ):
        QwenPipelineRunner(
            batch_runner=batch_runner,
            analysis_targets=[],
            sentiment_classifier=Mock(),
        )


def test_run_analysis_phase_calls_geo_analysis(
        tmp_path: Path,
        monkeypatch,
) -> None:
    import asyncio

    from app.qwen.analysis.models import (
        MentionTarget,
    )

    batch_runner = Mock()
    batch_runner.output_dir = tmp_path

    classifier = Mock()

    targets = [
        MentionTarget(
            target_id="hongmao",
            aliases=["鸿茅药酒"],
        )
    ]

    expected = Mock()

    async def fake_geo_analysis(
            batch_dir,
            passed_targets,
            passed_classifier,
    ):
        assert batch_dir == tmp_path
        assert passed_targets == targets
        assert (
                passed_classifier
                is classifier
        )

        return expected

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_geo_analysis",
        fake_geo_analysis,
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
        analysis_targets=targets,
        sentiment_classifier=(
            classifier
        ),
    )

    result = (
        pipeline.run_analysis_phase()
    )

    assert result is expected


def test_analysis_errors_make_pipeline_partial(
        tmp_path: Path,
) -> None:
    from app.qwen.analysis.models import (
        MentionTarget,
    )

    batch_runner = Mock()
    batch_runner.output_dir = (
            tmp_path / "batch"
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
        analysis_targets=[
            MentionTarget(
                target_id="hongmao",
                aliases=["鸿茅药酒"],
            )
        ],
        sentiment_classifier=Mock(),
    )

    summary = build_summary(
        pass_count=2,
    )

    analysis = Mock()
    analysis.sentiment.details = [
        Mock(
            sentiment_status="success"
        ),
        Mock(
            sentiment_status="timeout"
        ),
    ]

    pipeline.run_batch_phase = Mock(
        return_value=summary
    )

    pipeline.run_analysis_phase = Mock(
        return_value=analysis
    )

    pipeline.run_package_phase = Mock(
        return_value=(
                tmp_path / "package.zip"
        )
    )

    pipeline.run_analysis_persistence_phase = Mock(
        return_value=(
            tmp_path
            / "batch"
            / "geo_analysis_result.json",
            tmp_path
            / "batch"
            / "geo_analysis_metrics.json",
        )
    )

    result = pipeline.run(
        [],
        package_path=(
                tmp_path / "package.zip"
        ),
        batch_id="test",
        product_id="hongmao",
        product_name="????",
    )

    assert result.status == "partial"

    assert (
            result.analysis_status
            == "completed_with_warnings"
    )

    assert (
            result.analysis_error_count
            == 1
    )

    assert (
            result.analysis_verified
            is True
    )


def test_analysis_success_is_persisted(
        tmp_path: Path,
) -> None:
    from app.qwen.analysis.models import (
        MentionTarget,
    )

    batch_runner = Mock()
    batch_runner.output_dir = (
            tmp_path / "batch"
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
        analysis_targets=[
            MentionTarget(
                target_id="hongmao",
                aliases=["鸿茅药酒"],
            )
        ],
        sentiment_classifier=Mock(),
    )

    summary = build_summary(
        pass_count=2,
    )

    analysis = Mock()
    analysis.sentiment.details = []

    result_path = (
            tmp_path
            / "batch"
            / "geo_analysis_result.json"
    )

    metrics_path = (
            tmp_path
            / "batch"
            / "geo_analysis_metrics.json"
    )

    pipeline.run_batch_phase = Mock(
        return_value=summary
    )

    pipeline.run_analysis_phase = Mock(
        return_value=analysis
    )

    pipeline.run_package_phase = Mock(
        return_value=(
                tmp_path / "package.zip"
        )
    )

    pipeline.run_analysis_persistence_phase = Mock(
        return_value=(
            result_path,
            metrics_path,
        )
    )

    result = pipeline.run(
        [],
        package_path=(
                tmp_path / "package.zip"
        ),
        batch_id="test",
        product_id="hongmao",
        product_name="????",
    )

    assert result.status == "completed"

    assert (
            result.analysis_status
            == "completed"
    )

    assert (
            result.analysis_result_path
            == result_path
    )

    assert (
            result.analysis_metrics_path
            == metrics_path
    )

    assert result.analysis_verified


def test_analysis_failure_fails_pipeline(
        tmp_path: Path,
) -> None:
    from app.qwen.analysis.models import (
        MentionTarget,
    )

    batch_runner = Mock()
    batch_runner.output_dir = (
            tmp_path / "batch"
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
        analysis_targets=[
            MentionTarget(
                target_id="hongmao",
                aliases=["鸿茅药酒"],
            )
        ],
        sentiment_classifier=Mock(),
    )

    summary = build_summary(
        pass_count=2,
    )

    pipeline.run_batch_phase = Mock(
        return_value=summary
    )

    pipeline.run_analysis_phase = Mock(
        side_effect=ValueError(
            "analysis broken"
        )
    )

    pipeline.run_package_phase = Mock()

    result = pipeline.run(
        [],
        package_path=(
                tmp_path / "package.zip"
        ),
        batch_id="test",
        product_id="hongmao",
        product_name="????",
    )

    assert result.status == "failed"

    assert (
            result.analysis_status
            == "failed"
    )

    assert not (
        result.analysis_verified
    )

    pipeline.run_package_phase.assert_not_called()


def test_run_analysis_phase_works_with_running_event_loop(
        tmp_path: Path,
        monkeypatch,
) -> None:
    import asyncio
    import threading

    from app.qwen.analysis.models import (
        MentionTarget,
    )

    batch_runner = Mock()
    batch_runner.output_dir = tmp_path

    classifier = Mock()

    targets = [
        MentionTarget(
            target_id="hongmao",
            aliases=[
                "鸿茅药酒",
            ],
        )
    ]

    expected = Mock()

    main_thread_id = (
        threading.get_ident()
    )

    worker_thread_ids = []

    async def fake_geo_analysis(
            batch_dir,
            passed_targets,
            passed_classifier,
    ):
        worker_thread_ids.append(
            threading.get_ident()
        )

        assert batch_dir == tmp_path
        assert passed_targets == targets
        assert (
                passed_classifier
                is classifier
        )

        return expected

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_geo_analysis",
        fake_geo_analysis,
    )

    pipeline = QwenPipelineRunner(
        batch_runner=batch_runner,
        analysis_targets=targets,
        sentiment_classifier=(
            classifier
        ),
    )

    async def invoke():
        # 当前线程此时已有运行中的
        # asyncio event loop。
        return (
            pipeline.run_analysis_phase()
        )

    result = asyncio.run(
        invoke()
    )

    assert result is expected

    assert len(
        worker_thread_ids
    ) == 1

    assert (
            worker_thread_ids[0]
            != main_thread_id
    )
