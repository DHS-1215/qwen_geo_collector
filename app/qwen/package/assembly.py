from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.qwen.package.mapping import (
    answer_result_to_package_answer,
    answer_result_to_package_sources,
    task_run_to_package_task,
)
from app.qwen.package.models import (
    QwenPackageAnswer,
    QwenPackageSource,
    QwenPackageTask,
)
from app.qwen.package.reader import (
    load_answer_result,
    load_batch_summary,
)


@dataclass
class QwenPackageRecords:
    tasks: list[QwenPackageTask]
    answers: list[QwenPackageAnswer]
    sources: list[QwenPackageSource]


def assemble_package_records(
        batch_dir: str | Path,
) -> QwenPackageRecords:
    batch_dir = Path(
        batch_dir
    )

    summary = load_batch_summary(
        batch_dir
    )

    if summary.pending_count > 0:
        raise ValueError(
            "batch still has pending tasks; "
            "resume collection before package export"
        )

    package_tasks: list[
        QwenPackageTask
    ] = []

    package_answers: list[
        QwenPackageAnswer
    ] = []

    package_sources: list[
        QwenPackageSource
    ] = []

    for task_result in summary.task_results:
        package_tasks.append(
            task_run_to_package_task(
                task_result
            )
        )

        # 只有 PASS 才应该存在正式回答文件
        if task_result.status != "pass":
            continue

        answer_path = (
            batch_dir
            / (
                f"{task_result.question_id}_"
                f"{task_result.mode}.json"
            )
        )

        answer_result = load_answer_result(
            answer_path
        )

        # 防止目录中错误文件被误配到任务
        if (
                answer_result.question_id
                != task_result.question_id
        ):
            raise ValueError(
                "answer question_id mismatch: "
                f"{answer_path}"
            )

        if (
                answer_result.mode
                != task_result.mode
        ):
            raise ValueError(
                "answer mode mismatch: "
                f"{answer_path}"
            )

        package_answers.append(
            answer_result_to_package_answer(
                answer_result
            )
        )

        package_sources.extend(
            answer_result_to_package_sources(
                answer_result
            )
        )

    return QwenPackageRecords(
        tasks=package_tasks,
        answers=package_answers,
        sources=package_sources,
    )