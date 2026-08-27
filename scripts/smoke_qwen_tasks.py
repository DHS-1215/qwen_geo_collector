from __future__ import annotations

from collections import Counter
from pathlib import Path

from app.qwen.tasks import (
    load_tasks_csv,
)

ROOT_DIR = Path(
    __file__
).resolve().parents[1]


def main() -> None:
    input_path = (
            ROOT_DIR
            / "input"
            / "questions.csv"
    )

    tasks = load_tasks_csv(
        input_path
    )

    print(
        "[TASK COUNT]",
        len(tasks),
    )

    mode_counts = Counter(
        task.mode
        for task in tasks
    )

    print(
        "[QUICK COUNT]",
        mode_counts.get(
            "quick",
            0,
        ),
    )

    print(
        "[RESEARCH COUNT]",
        mode_counts.get(
            "research",
            0,
        ),
    )

    print()

    for index, task in enumerate(
            tasks,
            start=1,
    ):
        print(
            f"[TASK {index}]",
            task.question_id,
            task.mode,
        )

        print(
            "         ",
            task.question,
        )

    print()
    print(
        "[PASS] task CSV smoke completed"
    )


if __name__ == "__main__":
    main()
