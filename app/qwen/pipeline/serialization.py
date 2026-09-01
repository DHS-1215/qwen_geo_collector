from __future__ import annotations

import json
from pathlib import Path

from app.qwen.pipeline.models import (
    QwenPipelineResult,
)


def write_pipeline_result(
    result: QwenPipelineResult,
    path: str | Path,
) -> Path:
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = result.model_dump(
        mode="json"
    )

    data["batch_dir"] = (
        result.batch_dir.as_posix()
    )

    if result.package_path is not None:
        data["package_path"] = (
            result.package_path.as_posix()
        )

    if (
        result.analysis_result_path
        is not None
    ):
        data[
            "analysis_result_path"
        ] = (
            result.analysis_result_path
            .as_posix()
        )

    if (
        result.analysis_metrics_path
        is not None
    ):
        data[
            "analysis_metrics_path"
        ] = (
            result.analysis_metrics_path
            .as_posix()
        )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return path
