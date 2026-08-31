from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.qwen.batch import QwenBatchRunner
from app.qwen.models import QwenBatchSummary
from app.qwen.package.exporter import export_package_zip
from app.qwen.package.reader import load_batch_summary
from app.qwen.package.verifier import verify_package_zip
from app.qwen.pipeline.gates import (
    can_export_package,
    resolve_post_batch_status,
)
from app.qwen.pipeline.models import QwenPipelineResult
from app.qwen.tasks import QwenTask


class QwenPipelineRunner:
    def __init__(
        self,
        *,
        batch_runner: QwenBatchRunner,
    ) -> None:
        self.batch_runner = batch_runner
        self.batch_dir = Path(
            batch_runner.output_dir
        )

    def run_batch_phase(
        self,
        tasks: list[QwenTask],
        *,
        resume: bool = False,
    ) -> QwenBatchSummary:
        self.batch_runner.run(
            tasks,
            resume=resume,
        )

        return load_batch_summary(
            self.batch_dir
        )

    def run_package_phase(
        self,
        summary: QwenBatchSummary,
        *,
        package_path: Path,
        package_id: str,
    ) -> Path:
        if not can_export_package(summary):
            raise ValueError(
                "batch is blocked or still has pending tasks; "
                "resume collection before package export"
            )

        package_path = Path(
            package_path
        )

        export_package_zip(
            batch_dir=self.batch_dir,
            output_zip=package_path,
            package_id=package_id,
        )

        verify_package_zip(
            package_path
        )

        return package_path

    def run(
        self,
        tasks: list[QwenTask],
        *,
        package_path: Path,
        package_id: str,
        resume: bool = False,
    ) -> QwenPipelineResult:
        started_at = datetime.now()

        summary: QwenBatchSummary | None = None

        try:
            summary = self.run_batch_phase(
                tasks,
                resume=resume,
            )

            post_batch_status = (
                resolve_post_batch_status(
                    summary
                )
            )

            if post_batch_status == "blocked":
                return QwenPipelineResult(
                    status="blocked",
                    batch_dir=self.batch_dir,
                    package_path=None,
                    planned_count=(
                        summary.planned_count
                    ),
                    pass_count=(
                        summary.pass_count
                    ),
                    fail_count=(
                        summary.fail_count
                    ),
                    blocked_count=(
                        summary.blocked_count
                    ),
                    pending_count=(
                        summary.pending_count
                    ),
                    package_verified=False,
                    started_at=started_at,
                    finished_at=datetime.now(),
                )

            final_package_path = (
                self.run_package_phase(
                    summary,
                    package_path=package_path,
                    package_id=package_id,
                )
            )

            return QwenPipelineResult(
                status=post_batch_status,
                batch_dir=self.batch_dir,
                package_path=(
                    final_package_path
                ),
                planned_count=(
                    summary.planned_count
                ),
                pass_count=(
                    summary.pass_count
                ),
                fail_count=(
                    summary.fail_count
                ),
                blocked_count=(
                    summary.blocked_count
                ),
                pending_count=(
                    summary.pending_count
                ),
                package_verified=True,
                started_at=started_at,
                finished_at=datetime.now(),
            )

        except Exception as exc:
            if summary is None:
                planned_count = len(tasks)
                pass_count = 0
                fail_count = 0
                blocked_count = 0
                pending_count = len(tasks)
            else:
                planned_count = (
                    summary.planned_count
                )
                pass_count = (
                    summary.pass_count
                )
                fail_count = (
                    summary.fail_count
                )
                blocked_count = (
                    summary.blocked_count
                )
                pending_count = (
                    summary.pending_count
                )

            return QwenPipelineResult(
                status="failed",
                batch_dir=self.batch_dir,
                package_path=None,
                planned_count=planned_count,
                pass_count=pass_count,
                fail_count=fail_count,
                blocked_count=blocked_count,
                pending_count=pending_count,
                package_verified=False,
                error_type=(
                    type(exc).__name__
                ),
                error_message=str(exc),
                started_at=started_at,
                finished_at=datetime.now(),
            )