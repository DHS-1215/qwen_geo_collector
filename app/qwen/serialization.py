from __future__ import annotations

import json
from pathlib import Path

from app.qwen.models import (
    QwenAnswerResult,
)


def result_to_dict(
        result: QwenAnswerResult,
) -> dict:
    return result.model_dump(
        mode="json"
    )


def write_result_json(
        result: QwenAnswerResult,
        output_path: str | Path,
) -> Path:
    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = result_to_dict(
        result
    )

    output_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_path
