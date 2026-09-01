from __future__ import annotations

import argparse
from pathlib import Path

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment_config import (
    load_sentiment_config,
)
from app.qwen.analysis.sentiment_factory import (
    create_sentiment_classifier,
)
from app.qwen.batch import QwenBatchRunner
from app.qwen.browser import QwenBrowserSession
from app.qwen.exceptions import (
    QwenConnectionError,
)
from app.qwen.pipeline.runner import (
    QwenPipelineRunner,
)
from app.qwen.runner import QwenRunner
from app.qwen.tasks import load_tasks_csv


EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_CLI_ERROR = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qwen-geo-pipeline",
        description=(
            "Alibaba Qianwen GEO collection, "
            "analysis, package export and "
            "verification pipeline"
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
        "--target-id",
        required=True,
        help=(
            "Analysis target identifier, "
            "for example hongmao"
        ),
    )

    parser.add_argument(
        "--target-alias",
        action="append",
        required=True,
        help=(
            "Analysis target alias. "
            "Repeat this option for "
            "multiple aliases."
        ),
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


def _print_cli_error(
    exc: Exception,
) -> None:
    print(
        "[CLI ERROR]"
    )

    print(
        "[ERROR TYPE]",
        type(exc).__name__,
    )

    print(
        "[ERROR MESSAGE]",
        str(exc),
    )


def _build_target(
    *,
    target_id: str,
    aliases: list[str],
) -> MentionTarget:
    normalized_target_id = (
        target_id.strip()
    )

    if not normalized_target_id:
        raise ValueError(
            "target id cannot be empty"
        )

    normalized_aliases: list[str] = []

    seen: set[str] = set()

    for alias in aliases:
        normalized = alias.strip()

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        normalized_aliases.append(
            normalized
        )

    if not normalized_aliases:
        raise ValueError(
            "at least one non-empty "
            "target alias is required"
        )

    return MentionTarget(
        target_id=(
            normalized_target_id
        ),
        aliases=normalized_aliases,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        tasks = load_tasks_csv(
            args.input
        )

        target = _build_target(
            target_id=args.target_id,
            aliases=args.target_alias,
        )

        sentiment_config = (
            load_sentiment_config()
        )

        sentiment_classifier = (
            create_sentiment_classifier(
                sentiment_config
            )
        )

    except (
        FileNotFoundError,
        ValueError,
        UnicodeDecodeError,
    ) as exc:
        _print_cli_error(
            exc
        )

        return EXIT_CLI_ERROR

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

    print(
        "[TARGET ID]",
        target.target_id,
    )

    print(
        "[TARGET ALIASES]",
        ", ".join(
            target.aliases
        ),
    )

    print(
        "[SENTIMENT PROVIDER]",
        sentiment_config.provider,
    )

    print(
        "[SENTIMENT MODEL]",
        sentiment_config.model,
    )

    session = QwenBrowserSession()

    try:
        try:
            page = session.connect()

        except QwenConnectionError as exc:
            _print_cli_error(
                exc
            )

            return EXIT_CLI_ERROR

        runner = QwenRunner(
            page
        )

        batch_runner = QwenBatchRunner(
            runner=runner,
            output_dir=args.output,
        )

        pipeline = QwenPipelineRunner(
            batch_runner=batch_runner,
            analysis_targets=[
                target
            ],
            sentiment_classifier=(
                sentiment_classifier
            ),
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

        print(
            "[ANALYSIS STATUS]",
            result.analysis_status,
        )

        print(
            "[ANALYSIS VERIFIED]",
            result.analysis_verified,
        )

        print(
            "[ANALYSIS ERROR COUNT]",
            result.analysis_error_count,
        )

        if (
            result.package_path
            is not None
        ):
            print(
                "[PACKAGE OUTPUT]",
                result.package_path,
            )

        if (
            result.analysis_result_path
            is not None
        ):
            print(
                "[ANALYSIS RESULT]",
                result.analysis_result_path,
            )

        if (
            result.analysis_metrics_path
            is not None
        ):
            print(
                "[ANALYSIS METRICS]",
                result.analysis_metrics_path,
            )

        if result.status == "blocked":
            print(
                "[PIPELINE BLOCKED] "
                "Resume collection after "
                "manual verification."
            )

            return EXIT_BLOCKED

        if result.status == "failed":
            print(
                "[ERROR TYPE]",
                result.error_type,
            )

            print(
                "[ERROR MESSAGE]",
                result.error_message,
            )

            return EXIT_FAILED

        print(
            "[PIPELINE PASS]"
        )

        return EXIT_OK

    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
