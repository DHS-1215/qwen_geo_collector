from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Sequence

from app.qwen.analysis.geo_models import (
    GeoAnalysisBundle,
)
from app.qwen.analysis.geo_runner import (
    run_geo_analysis,
)
from app.qwen.analysis.geo_serialization import (
    write_geo_analysis_metrics,
    write_geo_analysis_result,
)
from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment import (
    SentimentClassifier,
)
from app.qwen.batch import QwenBatchRunner
from app.qwen.models import QwenBatchSummary
from app.qwen.package.exporter import (
    export_package_zip,
)
from app.qwen.package.reader import (
    load_batch_summary,
)
from app.qwen.package.verifier import (
    verify_package_zip,
)
from app.qwen.pipeline.gates import (
    can_export_package,
    resolve_post_batch_status,
)
from app.qwen.pipeline.models import (
    QwenPipelineResult,
)
from app.qwen.pipeline.serialization import (
    write_pipeline_result,
)
from app.qwen.tasks import QwenTask


ANALYSIS_ERROR_STATUSES = {
    "failed",
    "rate_limited",
    "timeout",
}


class QwenPipelineRunner:
    def __init__(
        self,
        *,
        batch_runner: QwenBatchRunner,
        analysis_targets: (
            Sequence[MentionTarget]
            | None
        ) = None,
        sentiment_classifier: (
            SentimentClassifier
            | None
        ) = None,
    ) -> None:
        self.batch_runner = batch_runner

        self.batch_dir = Path(
            batch_runner.output_dir
        )

        if (
            analysis_targets is None
        ) != (
            sentiment_classifier is None
        ):
            raise ValueError(
                "analysis_targets and "
                "sentiment_classifier must "
                "be configured together"
            )

        self.analysis_targets = (
            list(analysis_targets)
            if analysis_targets
            is not None
            else None
        )

        if (
                self.analysis_targets
                is not None
                and not self.analysis_targets
        ):
            raise ValueError(
                "analysis_targets cannot be empty"
            )

        self.sentiment_classifier = (
            sentiment_classifier
        )

    @property
    def analysis_enabled(
        self,
    ) -> bool:
        return (
            self.analysis_targets
            is not None
            and self.sentiment_classifier
            is not None
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

    def run_analysis_phase(
        self,
    ) -> GeoAnalysisBundle:
        if not self.analysis_enabled:
            raise ValueError(
                "GEO analysis is not configured"
            )

        assert (
            self.analysis_targets
            is not None
        )

        assert (
            self.sentiment_classifier
            is not None
        )

        return asyncio.run(
            run_geo_analysis(
                self.batch_dir,
                self.analysis_targets,
                self.sentiment_classifier,
            )
        )

    @staticmethod
    def count_analysis_errors(
        analysis: GeoAnalysisBundle,
    ) -> int:
        return sum(
            1
            for item
            in analysis.sentiment.details
            if item.sentiment_status
            in ANALYSIS_ERROR_STATUSES
        )

    def run_analysis_persistence_phase(
        self,
        analysis: GeoAnalysisBundle,
    ) -> tuple[Path, Path]:
        result_path = (
            self.batch_dir
            / "geo_analysis_result.json"
        )

        metrics_path = (
            self.batch_dir
            / "geo_analysis_metrics.json"
        )

        write_geo_analysis_result(
            analysis,
            result_path,
        )

        write_geo_analysis_metrics(
            analysis.metrics,
            metrics_path,
        )

        # 最小验证：
        # 使用现有 Pydantic 模型对刚写出的
        # JSON 做一次完整反序列化。
        GeoAnalysisBundle.model_validate_json(
            result_path.read_text(
                encoding="utf-8"
            )
        )

        type(
            analysis.metrics
        ).model_validate_json(
            metrics_path.read_text(
                encoding="utf-8"
            )
        )

        return (
            result_path,
            metrics_path,
        )

    def run_package_phase(
        self,
        summary: QwenBatchSummary,
        *,
        package_path: Path,
        package_id: str,
    ) -> Path:
        if not can_export_package(
            summary
        ):
            raise ValueError(
                "batch is blocked or still has "
                "pending tasks; resume collection "
                "before package export"
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

    def _finalize_result(
        self,
        result: QwenPipelineResult,
    ) -> QwenPipelineResult:
        write_pipeline_result(
            result,
            self.batch_dir
            / "pipeline_result.json",
        )

        return result

    def run(
        self,
        tasks: list[QwenTask],
        *,
        package_path: Path,
        package_id: str,
        resume: bool = False,
    ) -> QwenPipelineResult:
        started_at = datetime.now()

        summary: (
            QwenBatchSummary
            | None
        ) = None

        analysis: (
            GeoAnalysisBundle
            | None
        ) = None

        analysis_status = "not_run"
        analysis_error_count = 0

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
                return self._finalize_result(
                    QwenPipelineResult(
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
                        analysis_status=(
                            "not_run"
                        ),
                        analysis_verified=False,
                        started_at=started_at,
                        finished_at=datetime.now(),
                    )
                )

            if self.analysis_enabled:
                try:
                    analysis = (
                        self.run_analysis_phase()
                    )
                except Exception:
                    analysis_status = (
                        "failed"
                    )
                    raise

                analysis_error_count = (
                    self.count_analysis_errors(
                        analysis
                    )
                )

                analysis_status = (
                    "completed_with_warnings"
                    if analysis_error_count > 0
                    else "completed"
                )

            final_package_path = (
                self.run_package_phase(
                    summary,
                    package_path=package_path,
                    package_id=package_id,
                )
            )

            analysis_result_path = None
            analysis_metrics_path = None
            analysis_verified = False

            if analysis is not None:
                (
                    analysis_result_path,
                    analysis_metrics_path,
                ) = (
                    self
                    .run_analysis_persistence_phase(
                        analysis
                    )
                )

                analysis_verified = True

            final_status = (
                post_batch_status
            )

            if (
                analysis_error_count > 0
                and final_status
                == "completed"
            ):
                final_status = "partial"

            return self._finalize_result(
                QwenPipelineResult(
                    status=final_status,
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
                    analysis_status=(
                        analysis_status
                    ),
                    analysis_result_path=(
                        analysis_result_path
                    ),
                    analysis_metrics_path=(
                        analysis_metrics_path
                    ),
                    analysis_verified=(
                        analysis_verified
                    ),
                    analysis_error_count=(
                        analysis_error_count
                    ),
                    started_at=started_at,
                    finished_at=datetime.now(),
                )
            )

        except Exception as exc:
            if summary is None:
                planned_count = len(
                    tasks
                )
                pass_count = 0
                fail_count = 0
                blocked_count = 0
                pending_count = len(
                    tasks
                )

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

            return self._finalize_result(
                QwenPipelineResult(
                    status="failed",
                    batch_dir=self.batch_dir,
                    package_path=None,
                    planned_count=(
                        planned_count
                    ),
                    pass_count=pass_count,
                    fail_count=fail_count,
                    blocked_count=(
                        blocked_count
                    ),
                    pending_count=(
                        pending_count
                    ),
                    package_verified=False,
                    analysis_status=(
                        analysis_status
                    ),
                    analysis_verified=False,
                    analysis_error_count=(
                        analysis_error_count
                    ),
                    error_type=(
                        type(exc).__name__
                    ),
                    error_message=str(
                        exc
                    ),
                    started_at=started_at,
                    finished_at=datetime.now(),
                )
            )
