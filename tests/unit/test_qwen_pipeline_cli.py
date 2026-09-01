from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.exceptions import (
    QwenConnectionError,
)
from app.qwen.pipeline import (
    cli as pipeline_cli,
)


def build_pipeline_result(
    *,
    status: str = "completed",
):
    return SimpleNamespace(
        status=status,
        pass_count=1,
        fail_count=0,
        blocked_count=(
            1
            if status == "blocked"
            else 0
        ),
        pending_count=(
            2
            if status == "blocked"
            else 0
        ),
        package_verified=(
            status
            in {
                "completed",
                "partial",
            }
        ),
        package_path=(
            Path(
                "output/package.zip"
            )
            if status
            in {
                "completed",
                "partial",
            }
            else None
        ),
        analysis_status=(
            "completed"
            if status
            in {
                "completed",
                "partial",
            }
            else "not_run"
        ),
        analysis_verified=(
            status
            in {
                "completed",
                "partial",
            }
        ),
        analysis_error_count=0,
        analysis_result_path=(
            Path(
                "output/run_001/"
                "geo_analysis_result.json"
            )
            if status
            in {
                "completed",
                "partial",
            }
            else None
        ),
        analysis_metrics_path=(
            Path(
                "output/run_001/"
                "geo_analysis_metrics.json"
            )
            if status
            in {
                "completed",
                "partial",
            }
            else None
        ),
        error_type=(
            "ValueError"
            if status == "failed"
            else None
        ),
        error_message=(
            "模拟 Pipeline 失败"
            if status == "failed"
            else None
        ),
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

    sentiment_config = (
        SimpleNamespace(
            provider="ollama",
            model="qwen2.5:7b",
        )
    )

    load_config = Mock(
        return_value=(
            sentiment_config
        )
    )

    classifier = Mock()

    create_classifier = Mock(
        return_value=classifier
    )

    session = Mock()
    page = Mock()

    session.connect.return_value = (
        page
    )

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
        "load_sentiment_config",
        load_config,
    )

    monkeypatch.setattr(
        pipeline_cli,
        "create_sentiment_classifier",
        create_classifier,
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
        "sentiment_config": (
            sentiment_config
        ),
        "load_config": load_config,
        "classifier": classifier,
        "create_classifier": (
            create_classifier
        ),
        "session": session,
        "session_factory": (
            session_factory
        ),
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
        "--target-id",
        "hongmao",
        "--target-alias",
        "鸿茅药酒",
        "--target-alias",
        "鸿茅",
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


def test_build_parser_parses_required_args():
    parser = (
        pipeline_cli.build_parser()
    )

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
            "--target-id",
            "hongmao",
            "--target-alias",
            "鸿茅药酒",
            "--target-alias",
            "鸿茅",
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

    assert (
        args.target_id
        == "hongmao"
    )

    assert args.target_alias == [
        "鸿茅药酒",
        "鸿茅",
    ]

    assert args.resume is True


def test_build_target_normalizes_aliases():
    target = pipeline_cli._build_target(
        target_id=" hongmao ",
        aliases=[
            " 鸿茅药酒 ",
            "鸿茅",
            "鸿茅",
            "",
        ],
    )

    assert target == MentionTarget(
        target_id="hongmao",
        aliases=[
            "鸿茅药酒",
            "鸿茅",
        ],
    )


def test_build_target_rejects_empty_aliases():
    try:
        pipeline_cli._build_target(
            target_id="hongmao",
            aliases=[
                "",
                "   ",
            ],
        )

    except ValueError as exc:
        assert (
            "at least one"
            in str(exc)
        )

    else:
        raise AssertionError(
            "expected ValueError"
        )


def test_main_completed_returns_zero(
    monkeypatch,
):
    set_cli_args(
        monkeypatch,
        resume=True,
    )

    result = build_pipeline_result()

    deps = (
        configure_cli_dependencies(
            monkeypatch,
            pipeline_result=result,
        )
    )

    exit_code = (
        pipeline_cli.main()
    )

    assert exit_code == 0

    deps[
        "load_tasks"
    ].assert_called_once_with(
        Path(
            "input/questions.csv"
        )
    )

    deps[
        "load_config"
    ].assert_called_once_with()

    deps[
        "create_classifier"
    ].assert_called_once_with(
        deps["sentiment_config"]
    )

    deps[
        "pipeline_factory"
    ].assert_called_once_with(
        batch_runner=(
            deps["batch_runner"]
        ),
        analysis_targets=[
            MentionTarget(
                target_id="hongmao",
                aliases=[
                    "鸿茅药酒",
                    "鸿茅",
                ],
            )
        ],
        sentiment_classifier=(
            deps["classifier"]
        ),
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
):
    set_cli_args(
        monkeypatch
    )

    result = build_pipeline_result(
        status="blocked"
    )

    deps = (
        configure_cli_dependencies(
            monkeypatch,
            pipeline_result=result,
        )
    )

    exit_code = (
        pipeline_cli.main()
    )

    assert exit_code == 2

    deps[
        "session"
    ].close.assert_called_once_with()


def test_main_failed_returns_one(
    monkeypatch,
):
    set_cli_args(
        monkeypatch
    )

    result = build_pipeline_result(
        status="failed"
    )

    deps = (
        configure_cli_dependencies(
            monkeypatch,
            pipeline_result=result,
        )
    )

    exit_code = (
        pipeline_cli.main()
    )

    assert exit_code == 1

    deps[
        "session"
    ].close.assert_called_once_with()


def test_main_returns_three_when_task_loading_fails(
    monkeypatch,
):
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

    exit_code = (
        pipeline_cli.main()
    )

    assert exit_code == (
        pipeline_cli.EXIT_CLI_ERROR
    )


def test_main_returns_three_when_sentiment_config_fails(
    monkeypatch,
):
    set_cli_args(
        monkeypatch
    )

    tasks = [
        Mock()
    ]

    monkeypatch.setattr(
        pipeline_cli,
        "load_tasks_csv",
        Mock(
            return_value=tasks
        ),
    )

    monkeypatch.setattr(
        pipeline_cli,
        "load_sentiment_config",
        Mock(
            side_effect=ValueError(
                "invalid sentiment config"
            )
        ),
    )

    session_factory = Mock()

    monkeypatch.setattr(
        pipeline_cli,
        "QwenBrowserSession",
        session_factory,
    )

    exit_code = (
        pipeline_cli.main()
    )

    assert exit_code == (
        pipeline_cli.EXIT_CLI_ERROR
    )

    session_factory.assert_not_called()


def test_main_returns_three_when_cdp_connection_fails(
    monkeypatch,
):
    set_cli_args(
        monkeypatch
    )

    result = build_pipeline_result()

    deps = (
        configure_cli_dependencies(
            monkeypatch,
            pipeline_result=result,
        )
    )

    deps[
        "session"
    ].connect.side_effect = (
        QwenConnectionError(
            "模拟 CDP 连接失败"
        )
    )

    exit_code = (
        pipeline_cli.main()
    )

    assert exit_code == (
        pipeline_cli.EXIT_CLI_ERROR
    )

    deps[
        "session"
    ].connect.assert_called_once_with()

    deps[
        "session"
    ].close.assert_called_once_with()
