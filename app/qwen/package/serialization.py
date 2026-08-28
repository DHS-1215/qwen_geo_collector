from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


def model_to_dict(
        model: BaseModel,
) -> dict:
    return model.model_dump(
        mode="json"
    )


def write_json(
        model: BaseModel,
        output_path: str | Path,
) -> Path:
    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = model_to_dict(
        model
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


def write_jsonl(
        models: list[BaseModel],
        output_path: str | Path,
) -> Path:
    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = []

    for model in models:
        data = model_to_dict(
            model
        )

        lines.append(
            json.dumps(
                data,
                ensure_ascii=False,
            )
        )

    content = "\n".join(
        lines
    )

    if lines:
        content += "\n"

    output_path.write_text(
        content,
        encoding="utf-8",
    )

    return output_path
