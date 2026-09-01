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
            "--batch-id",
            "qwen-test",
            "--product-id",
            "hongmao",
            "--product-name",
            "鸿茅药酒",
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
        args.batch_id
        == "qwen-test"
    )

    assert (
        args.product_id
        == "hongmao"
    )

    assert (
        args.product_name
        == "鸿茅药酒"
    )


def test_package_cli_package_id_alias() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(
        [
            "export",
            "--batch-dir",
            "output/cli_smoke",
            "--output",
            "output/package.zip",
            "--package-id",
            "legacy-name",
            "--product-id",
            "hongmao",
            "--product-name",
            "鸿茅药酒",
        ]
    )

    assert (
        args.batch_id
        == "legacy-name"
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

    def fake_export_central_package_zip(
            *,
            batch_dir,
            output_zip,
            batch_id,
            product_id,
            product_name,
    ):
        state["batch_dir"] = batch_dir
        state["output_zip"] = output_zip
        state["batch_id"] = batch_id
        state["product_id"] = product_id
        state["product_name"] = product_name

        return output_zip

    monkeypatch.setattr(
        cli,
        "export_central_package_zip",
        fake_export_central_package_zip,
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
            "--batch-id",
            "qwen-test",
            "--product-id",
            "hongmao",
            "--product-name",
            "鸿茅药酒",
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
        state["batch_id"]
        == "qwen-test"
    )

    assert (
        state["product_id"]
        == "hongmao"
    )

    assert (
        state["product_name"]
        == "鸿茅药酒"
    )


def test_package_cli_main_verify(
        monkeypatch,
) -> None:
    state = {}

    def fake_verify_central_package_zip(
            package_path,
    ) -> None:
        state[
            "package_path"
        ] = package_path

    monkeypatch.setattr(
        cli,
        "verify_central_package_zip",
        fake_verify_central_package_zip,
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
