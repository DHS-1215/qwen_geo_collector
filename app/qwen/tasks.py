from __future__ import annotations

import csv
from pathlib import Path

from pydantic import (
    BaseModel,
    field_validator,
)

VALID_MODES = {
    "quick",
    "research",
}


class QwenTask(BaseModel):
    question_id: str
    question: str
    mode: str

    @field_validator(
        "question_id",
        "question",
        mode="before",
    )
    @classmethod
    def strip_text(
            cls,
            value,
    ):
        if isinstance(value, str):
            value = value.strip()

        return value

    @field_validator(
        "question_id",
    )
    @classmethod
    def validate_question_id(
            cls,
            value: str,
    ) -> str:
        if not value:
            raise ValueError(
                "question_id 不能为空"
            )

        return value

    @field_validator(
        "question",
    )
    @classmethod
    def validate_question(
            cls,
            value: str,
    ) -> str:
        if not value:
            raise ValueError(
                "question 不能为空"
            )

        return value

    @field_validator(
        "mode",
    )
    @classmethod
    def validate_mode(
            cls,
            value: str,
    ) -> str:
        if value not in VALID_MODES:
            raise ValueError(
                f"不支持的 mode: {value}，"
                f"只允许 quick / research"
            )

        return value


def load_tasks_csv(
        path: str | Path,
) -> list[QwenTask]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"任务文件不存在: {path}"
        )

    tasks: list[QwenTask] = []

    seen_keys: set[
        tuple[str, str]
    ] = set()

    with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        required_columns = {
            "question_id",
            "question",
            "mode",
        }

        actual_columns = set(
            reader.fieldnames or []
        )

        missing_columns = (
                required_columns
                - actual_columns
        )

        if missing_columns:
            raise ValueError(
                "CSV 缺少字段: "
                + ", ".join(
                    sorted(
                        missing_columns
                    )
                )
            )

        for row_number, row in enumerate(
                reader,
                start=2,
        ):
            try:
                task = QwenTask(
                    question_id=(
                        row.get(
                            "question_id",
                            ""
                        )
                    ),
                    question=(
                        row.get(
                            "question",
                            ""
                        )
                    ),
                    mode=(
                        row.get(
                            "mode",
                            ""
                        )
                    ),
                )

            except Exception as exc:
                raise ValueError(
                    f"CSV 第 {row_number} 行"
                    f"任务无效: {exc}"
                ) from exc

            key = (
                task.question_id,
                task.mode,
            )

            if key in seen_keys:
                raise ValueError(
                    f"CSV 第 {row_number} 行"
                    f"存在重复任务: "
                    f"{task.question_id} "
                    f"{task.mode}"
                )

            seen_keys.add(
                key
            )

            tasks.append(
                task
            )

    if not tasks:
        raise ValueError(
            "CSV 中没有任务"
        )

    return tasks
