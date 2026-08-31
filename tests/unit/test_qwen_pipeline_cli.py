from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from app.qwen.pipeline import cli as pipeline_cli

from app.qwen.exceptions import (
    QwenConnectionError,
)


def configure_cli_dependencies(
        monkeypatch,
        *,
        pipeline_result,
):
    tasks = [
        Mock(
            question_id="Q001",
            mode="quick",
        ),
    ]

    load_tasks = Mock(
        return_value=tasks
    )

    session = Mock()
    page = Mock()
    session.connect.return_value = page

    session_factory = Mock(
        return_value=session
    )

    qwen_runner = Mock()
    qwen_runner_factory = Mock(
        return_value=qwen_runner
    )

    batch_runner = Mock()
    batch_runner_factory = Mock(
        return_value=batch_runner
    )

    pipeline = Mock()
    pipeline.run.return_value = (
        pipeline_result
    )

    pipeline_factory = Mock(
        return_value=pipeline
    )

    monkeypatch.setattr(
        pipeline_cli,
        "load_tasks_csv",
        load_tasks,
    )

    monkeypatch.setattr(
        pipeline_cli,
        "QwenBrowserSession",
        session_factory,
    )

    monkeypatch.setattr(
        pipeline_cli,
        "QwenRunner",
        qwen_runner_factory,
    )

    monkeypatch.setattr(
        pipeline_cli,
        "QwenBatchRunner",
        batch_runner_factory,
    )

    monkeypatch.setattr(
        pipeline_cli,
        "QwenPipelineRunner",
        pipeline_factory,
    )

    return {
        "tasks": tasks,
        "load_tasks": load_tasks,
        "session": session,
        "session_factory": session_factory,
        "qwen_runner": qwen_runner,
        "qwen_runner_factory": (
            qwen_runner_factory
        ),
        "batch_runner": batch_runner,
        "batch_runner_factory": (
            batch_runner_factory
        ),
        "pipeline": pipeline,
        "pipeline_factory": (
            pipeline_factory
        ),
    }


def set_cli_args(
        monkeypatch,
        *,
        resume: bool = False,
) -> None:
    argv = [
        "qwen-geo-pipeline",
        "--input",
        "input/questions.csv",
        "--output",
        "output/run_001",
        "--package",
        "output/package.zip",
        "--package-id",
        "qwen-run-001",
    ]

    if resume:
        argv.append(
            "--resume"
        )

    monkeypatch.setattr(
        sys,
        "argv",
        argv,
    )


def test_build_parser_parses_required_args() -> None:
    parser = pipeline_cli.build_parser()

    args = parser.parse_args(
        [
            "--input",
            "input/questions.csv",
            "--output",
            "output/run_001",
            "--package",
            "output/package.zip",
            "--package-id",
            "qwen-run-001",
            "--resume",
        ]
    )

    assert args.input == Path(
        "input/questions.csv"
    )

    assert args.output == Path(
        "output/run_001"
    )

    assert args.package == Path(
        "output/package.zip"
    )

    assert (
            args.package_id
            == "qwen-run-001"
    )

    assert args.resume is True


def test_main_completed_returns_zero(
        monkeypatch,
) -> None:
    set_cli_args(
        monkeypatch,
        resume=True,
    )

    result = SimpleNamespace(
        status="completed",
        pass_count=1,
        fail_count=0,
        blocked_count=0,
        pending_count=0,
        package_verified=True,
        package_path=Path(
            "output/package.zip"
        ),
        error_type=None,
        error_message=None,
    )

    deps = configure_cli_dependencies(
        monkeypatch,
        pipeline_result=result,
    )

    exit_code = pipeline_cli.main()

    assert exit_code == 0

    deps[
        "load_tasks"
    ].assert_called_once_with(
        Path(
            "input/questions.csv"
        )
    )

    deps[
        "pipeline"
    ].run.assert_called_once_with(
        deps["tasks"],
        package_path=Path(
            "output/package.zip"
        ),
        package_id="qwen-run-001",
        resume=True,
    )

    deps[
        "session"
    ].close.assert_called_once_with()


def test_main_blocked_returns_two(
        monkeypatch,
) -> None:
    set_cli_args(
        monkeypatch
    )

    result = SimpleNamespace(
        status="blocked",
        pass_count=1,
        fail_count=0,
        blocked_count=1,
        pending_count=2,
        package_verified=False,
        package_path=None,
        error_type=None,
        error_message=None,
    )

    deps = configure_cli_dependencies(
        monkeypatch,
        pipeline_result=result,
    )

    exit_code = pipeline_cli.main()

    assert exit_code == 2

    deps[
        "session"
    ].close.assert_called_once_with()


def test_main_failed_returns_one(
        monkeypatch,
) -> None:
    set_cli_args(
        monkeypatch
    )

    result = SimpleNamespace(
        status="failed",
        pass_count=1,
        fail_count=0,
        blocked_count=0,
        pending_count=0,
        package_verified=False,
        package_path=None,
        error_type="ValueError",
        error_message="模拟验包失败",
    )

    deps = configure_cli_dependencies(
        monkeypatch,
        pipeline_result=result,
    )

    exit_code = pipeline_cli.main()

    assert exit_code == 1

    deps[
        "session"
    ].close.assert_called_once_with()


def test_main_returns_three_when_task_loading_fails(
        monkeypatch,
) -> None:
    set_cli_args(
        monkeypatch
    )

    load_tasks = Mock(
        side_effect=ValueError(
            "模拟 CSV 格式错误"
        )
    )

    monkeypatch.setattr(
        pipeline_cli,
        "load_tasks_csv",
        load_tasks,
    )

    exit_code = pipeline_cli.main()

    assert exit_code == (
        pipeline_cli.EXIT_CLI_ERROR
    )

    load_tasks.assert_called_once_with(
        Path(
            "input/questions.csv"
        )
    )


def test_main_returns_three_when_cdp_connection_fails(
        monkeypatch,
) -> None:
    set_cli_args(
        monkeypatch
    )

    tasks = [
        Mock(
            question_id="Q001",
            mode="quick",
        ),
    ]

    monkeypatch.setattr(
        pipeline_cli,
        "load_tasks_csv",
        Mock(
            return_value=tasks
        ),
    )

    session = Mock()

    session.connect.side_effect = (
        QwenConnectionError(
            "模拟 CDP 连接失败"
        )
    )

    session_factory = Mock(
        return_value=session
    )

    monkeypatch.setattr(
        pipeline_cli,
        "QwenBrowserSession",
        session_factory,
    )

    exit_code = pipeline_cli.main()

    assert exit_code == (
        pipeline_cli.EXIT_CLI_ERROR
    )

    session.connect.assert_called_once_with()
    session.close.assert_called_once_with()
