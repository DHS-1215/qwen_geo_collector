from __future__ import annotations

import argparse
from pathlib import Path

from app.qwen.batch import QwenBatchRunner
from app.qwen.browser import QwenBrowserSession
from app.qwen.pipeline.runner import QwenPipelineRunner
from app.qwen.runner import QwenRunner
from app.qwen.tasks import load_tasks_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qwen-geo-pipeline",
        description=(
            "Alibaba Qianwen GEO collection, "
            "package export and verification pipeline"
        ),
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to task CSV file",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory for collection outputs",
    )

    parser.add_argument(
        "--package",
        type=Path,
        required=True,
        help="Path to final GEO package ZIP",
    )

    parser.add_argument(
        "--package-id",
        required=True,
        help="Unique GEO package identifier",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume an existing batch and "
            "skip tasks already marked PASS"
        ),
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    tasks = load_tasks_csv(
        args.input
    )

    print(
        "[INPUT]",
        args.input,
    )

    print(
        "[OUTPUT]",
        args.output,
    )

    print(
        "[PACKAGE]",
        args.package,
    )

    print(
        "[PACKAGE ID]",
        args.package_id,
    )

    print(
        "[RESUME]",
        args.resume,
    )

    print(
        "[TASK COUNT]",
        len(tasks),
    )

    session = QwenBrowserSession()

    try:
        page = session.connect()

        runner = QwenRunner(
            page
        )

        batch_runner = QwenBatchRunner(
            runner=runner,
            output_dir=args.output,
        )

        pipeline = QwenPipelineRunner(
            batch_runner=batch_runner,
        )

        result = pipeline.run(
            tasks,
            package_path=args.package,
            package_id=args.package_id,
            resume=args.resume,
        )

        print()

        print(
            "[PIPELINE STATUS]",
            result.status,
        )

        print(
            "[PASS]",
            result.pass_count,
        )

        print(
            "[FAIL]",
            result.fail_count,
        )

        print(
            "[BLOCKED]",
            result.blocked_count,
        )

        print(
            "[PENDING]",
            result.pending_count,
        )

        print(
            "[PACKAGE VERIFIED]",
            result.package_verified,
        )

        if result.package_path is not None:
            print(
                "[PACKAGE OUTPUT]",
                result.package_path,
            )

        if result.status == "blocked":
            print(
                "[PIPELINE BLOCKED] "
                "Resume collection after "
                "manual verification."
            )
            return 2

        if result.status == "failed":
            print(
                "[ERROR TYPE]",
                result.error_type,
            )

            print(
                "[ERROR MESSAGE]",
                result.error_message,
            )

            return 1

        print(
            "[PIPELINE PASS]"
        )

        return 0

    finally:
        session.close()
