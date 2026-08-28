from __future__ import annotations

from pathlib import Path

import app.qwen.package.cli as cli


def test_package_cli_parser_export() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(
        [
            "export",
            "--batch-dir",
            "output/cli_smoke",
            "--output",
            "output/package.zip",
            "--package-id",
            "qwen-test",
        ]
    )

    assert args.command == "export"

    assert (
            args.batch_dir
            == Path(
        "output/cli_smoke"
    )
    )

    assert (
            args.output
            == Path(
        "output/package.zip"
    )
    )

    assert (
            args.package_id
            == "qwen-test"
    )


def test_package_cli_parser_verify() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(
        [
            "verify",
            "--package",
            "output/package.zip",
        ]
    )

    assert args.command == "verify"

    assert (
            args.package
            == Path(
        "output/package.zip"
    )
    )


def test_package_cli_main_export(
        monkeypatch,
) -> None:
    state = {}

    def fake_export_package_zip(
            *,
            batch_dir,
            output_zip,
            package_id,
    ):
        state[
            "batch_dir"
        ] = batch_dir

        state[
            "output_zip"
        ] = output_zip

        state[
            "package_id"
        ] = package_id

        return output_zip

    monkeypatch.setattr(
        cli,
        "export_package_zip",
        fake_export_package_zip,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "qwen-geo-package",
            "export",
            "--batch-dir",
            "output/cli_smoke",
            "--output",
            "output/package.zip",
            "--package-id",
            "qwen-test",
        ],
    )

    cli.main()

    assert (
            state["batch_dir"]
            == Path(
        "output/cli_smoke"
    )
    )

    assert (
            state["output_zip"]
            == Path(
        "output/package.zip"
    )
    )

    assert (
            state["package_id"]
            == "qwen-test"
    )


def test_package_cli_main_verify(
        monkeypatch,
) -> None:
    state = {}

    def fake_verify_package_zip(
            package_path,
    ) -> None:
        state[
            "package_path"
        ] = package_path

    monkeypatch.setattr(
        cli,
        "verify_package_zip",
        fake_verify_package_zip,
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "qwen-geo-package",
            "verify",
            "--package",
            "output/package.zip",
        ],
    )

    cli.main()

    assert (
            state["package_path"]
            == Path(
        "output/package.zip"
    )
    )
