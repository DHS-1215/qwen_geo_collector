from __future__ import annotations

from pathlib import Path

from types import SimpleNamespace

import app.qwen.cli as cli

from app.qwen.cli import (
    build_parser,
)


def test_cli_parser_basic_args() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "--input",
            "input/questions.csv",
            "--output",
            "output/run_001",
        ]
    )

    assert args.input == Path(
        "input/questions.csv"
    )

    assert args.output == Path(
        "output/run_001"
    )

    assert args.resume is False


def test_cli_parser_resume_flag() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "--input",
            "input/questions.csv",
            "--output",
            "output/run_001",
            "--resume",
        ]
    )

    assert args.resume is True


def test_cli_main_passes_resume_to_batch(
        monkeypatch,
) -> None:
    state = {
        "session_closed": False,
        "resume": None,
        "output_dir": None,
    }

    fake_tasks = [
        SimpleNamespace(
            question_id="Q001",
            question="测试问题",
            mode="quick",
        )
    ]

    fake_page = object()

    class FakeBrowserSession:
        def connect(self):
            return fake_page

        def close(self):
            state[
                "session_closed"
            ] = True

    class FakeRunner:
        def __init__(
                self,
                page,
        ):
            assert page is fake_page

    class FakeBatchRunner:
        def __init__(
                self,
                *,
                runner,
                output_dir,
        ):
            assert isinstance(
                runner,
                FakeRunner,
            )

            state[
                "output_dir"
            ] = output_dir

        def run(
                self,
                tasks,
                *,
                resume=False,
        ):
            assert tasks is fake_tasks

            state[
                "resume"
            ] = resume

            return [
                SimpleNamespace(
                    question_id="Q001",
                    mode="quick",
                    status="pass",
                )
            ]

    monkeypatch.setattr(
        cli,
        "load_tasks_csv",
        lambda path: fake_tasks,
    )

    monkeypatch.setattr(
        cli,
        "QwenBrowserSession",
        FakeBrowserSession,
    )

    monkeypatch.setattr(
        cli,
        "QwenRunner",
        FakeRunner,
    )

    monkeypatch.setattr(
        cli,
        "QwenBatchRunner",
        FakeBatchRunner,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "qwen-geo",
            "--input",
            "input/questions.csv",
            "--output",
            "output/run_001",
            "--resume",
        ],
    )

    cli.main()

    assert (
            state["resume"]
            is True
    )

    assert (
            state["output_dir"]
            == Path(
        "output/run_001"
    )
    )

    assert (
            state["session_closed"]
            is True
    )
