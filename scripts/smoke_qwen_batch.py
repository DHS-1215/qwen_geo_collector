from __future__ import annotations

from pathlib import Path

from app.qwen.batch import (
    QwenBatchRunner,
)
from app.qwen.browser import (
    QwenBrowserSession,
)
from app.qwen.runner import (
    QwenRunner,
)
from app.qwen.tasks import (
    load_tasks_csv,
)

ROOT_DIR = Path(
    __file__
).resolve().parents[1]


def main() -> None:
    tasks = load_tasks_csv(
        ROOT_DIR
        / "input"
        / "questions.csv"
    )

    # Smoke 暂时只跑前两条：
    # Q001 quick
    # Q001 research
    #
    # 这样既验证批处理，
    # 又不一次连续请求四题。
    smoke_tasks = tasks[:2]

    output_dir = (
            ROOT_DIR
            / "output"
            / "batch_resume_smoke"
    )

    session = QwenBrowserSession()

    try:
        page = session.connect()

        runner = QwenRunner(
            page
        )

        batch_runner = (
            QwenBatchRunner(
                runner=runner,
                output_dir=output_dir,
            )
        )

        results = batch_runner.run(
            smoke_tasks,
            resume=True,
        )

        print()
        print(
            "[SMOKE RESULT COUNT]",
            len(results),
        )

        for result in results:
            print(
                "[RESULT]",
                result.question_id,
                result.mode,
                result.status,
                result.output_path,
            )

        print()
        print(
            "[PASS] batch smoke completed"
        )

        print(
            "[OUTPUT DIR]",
            output_dir,
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()
