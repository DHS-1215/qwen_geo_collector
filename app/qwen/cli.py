from __future__ import annotations

import argparse
from pathlib import Path

from app.qwen.batch import (
    QwenBatchRunner,
)
from app.qwen.browser import (
    QwenBrowserSession,
)
from app.qwen.runner import (
    QwenRunner,
)
from app.qwen.tasks import (
    load_tasks_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qwen-geo",
        description=(
            "Alibaba Qianwen GEO batch collector"
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
        "--resume",
        action="store_true",
        help=(
            "Resume an existing batch and "
            "skip tasks already marked PASS"
        ),
    )

    return parser


def main() -> None:
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

        results = batch_runner.run(
            tasks,
            resume=args.resume,
        )

        print()

        print(
            "[CLI COMPLETE]"
        )

        print(
            "[RESULT COUNT]",
            len(results),
        )

        for result in results:
            print(
                "[RESULT]",
                result.question_id,
                result.mode,
                result.status,
            )

    finally:
        session.close()