from __future__ import annotations

import argparse
from pathlib import Path

from app.qwen.package.exporter import (
    export_package_zip,
)
from app.qwen.package.verifier import (
    verify_package_zip,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qwen-geo-package",
        description=(
            "Qwen GEO package export "
            "and verification tools"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # =========================================
    # export
    # =========================================

    export_parser = (
        subparsers.add_parser(
            "export",
            help=(
                "Export a Qwen GEO ZIP package"
            ),
        )
    )

    export_parser.add_argument(
        "--batch-dir",
        type=Path,
        required=True,
        help="Qwen batch output directory",
    )

    export_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output ZIP path",
    )

    export_parser.add_argument(
        "--package-id",
        required=True,
        help="Package identifier",
    )

    # =========================================
    # verify
    # =========================================

    verify_parser = (
        subparsers.add_parser(
            "verify",
            help=(
                "Verify a Qwen GEO ZIP package"
            ),
        )
    )

    verify_parser.add_argument(
        "--package",
        type=Path,
        required=True,
        help="Path to GEO ZIP package",
    )

    return parser


def main() -> None:
    parser = build_parser()

    args = parser.parse_args()

    if args.command == "export":
        result = export_package_zip(
            batch_dir=args.batch_dir,
            output_zip=args.output,
            package_id=args.package_id,
        )

        print(
            "[PACKAGE EXPORT PASS]",
            result,
        )

        return

    if args.command == "verify":
        verify_package_zip(
            args.package
        )

        print(
            "[PACKAGE VERIFY PASS]",
            args.package,
        )

        return

    parser.error(
        f"unsupported command: "
        f"{args.command}"
    )