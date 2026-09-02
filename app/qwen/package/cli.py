from __future__ import annotations

import argparse
from pathlib import Path

from app.qwen.package.exporter import (
    export_central_package_zip,
)
from app.qwen.package.verifier import (
    verify_central_package_zip,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qwen-geo-package",
        description=(
            "Qwen GEO central package export "
            "and verification tools"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    export_parser = (
        subparsers.add_parser(
            "export",
            help=(
                "Export a central "
                "geo_package_v1 ZIP"
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
        "--batch-id",
        "--package-id",
        dest="batch_id",
        required=True,
        help=(
            "Central GEO batch identifier. "
            "--package-id is kept as a "
            "compatibility alias."
        ),
    )

    export_parser.add_argument(
        "--product-id",
        required=True,
        help="Central GEO product identifier",
    )

    export_parser.add_argument(
        "--product-name",
        required=True,
        help="Central GEO product name",
    )

    verify_parser = (
        subparsers.add_parser(
            "verify",
            help=(
                "Verify a central "
                "geo_package_v1 ZIP"
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
        result = (
            export_central_package_zip(
                batch_dir=args.batch_dir,
                output_zip=args.output,
                batch_id=args.batch_id,
                product_id=args.product_id,
                product_name=args.product_name,
            )
        )

        print(
            "[PACKAGE EXPORT PASS]",
            result,
        )

        return

    if args.command == "verify":
        verify_central_package_zip(
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


if __name__ == "__main__":
    main()
