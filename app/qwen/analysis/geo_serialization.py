from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.qwen.analysis.geo_models import (
    GeoAnalysisBundle,
    GeoAnalysisMetrics,
)


def serialize_geo_analysis_result(
    bundle: GeoAnalysisBundle,
) -> dict[str, Any]:
    return bundle.model_dump(
        mode="json"
    )


def serialize_geo_analysis_metrics(
    metrics: GeoAnalysisMetrics,
) -> dict[str, Any]:
    return metrics.model_dump(
        mode="json"
    )


def write_geo_analysis_result(
    bundle: GeoAnalysisBundle,
    output_path: str | Path,
) -> Path:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            serialize_geo_analysis_result(
                bundle
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def write_geo_analysis_metrics(
    metrics: GeoAnalysisMetrics,
    output_path: str | Path,
) -> Path:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            serialize_geo_analysis_metrics(
                metrics
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path
