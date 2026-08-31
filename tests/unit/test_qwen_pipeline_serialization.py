from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.qwen.pipeline.models import (
    QwenPipelineResult,
)
from app.qwen.pipeline.serialization import (
    write_pipeline_result,
)


def test_write_pipeline_result(
        tmp_path: Path,
) -> None:
    result = QwenPipelineResult(
        status="completed",
        batch_dir=Path(
            "output/run_001"
        ),
        package_path=Path(
            "output/package.zip"
        ),
        planned_count=2,
        pass_count=2,
        fail_count=0,
        blocked_count=0,
        pending_count=0,
        package_verified=True,
        started_at=datetime(
            2026,
            8,
            31,
            9,
            0,
        ),
        finished_at=datetime(
            2026,
            8,
            31,
            9,
            10,
        ),
    )

    output_path = (
            tmp_path
            / "pipeline_result.json"
    )

    returned_path = (
        write_pipeline_result(
            result,
            output_path,
        )
    )

    assert returned_path == output_path
    assert output_path.exists()

    data = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
            data["status"]
            == "completed"
    )

    assert (
            data["batch_dir"]
            == "output/run_001"
    )

    assert (
            data["package_path"]
            == "output/package.zip"
    )

    assert (
            data["planned_count"]
            == 2
    )

    assert (
            data["package_verified"]
            is True
    )

    assert (
            data["started_at"]
            == "2026-08-31T09:00:00"
    )
