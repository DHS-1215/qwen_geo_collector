from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.qwen.browser import QwenBrowserSession
from app.qwen.runner import QwenRunner
from app.qwen.serialization import (
    write_result_json,
)

ROOT_DIR = Path(
    __file__
).resolve().parents[1]

QUICK_QUESTION = (
    "鸿茅药酒到底是药还是酒？"
)

RESEARCH_QUESTION = (
    "鸿茅药酒到底是药还是酒？"
    "请基于公开网页资料回答，并附参考来源。"
)


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
            ROOT_DIR
            / "output"
            / f"real_result_smoke_{timestamp}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    session = QwenBrowserSession()

    try:
        page = session.connect()

        runner = QwenRunner(
            page
        )

        # =====================================
        # Quick
        # =====================================

        print(
            "[RUN] Quick"
        )

        quick_result = runner.ask(
            QUICK_QUESTION,
            mode="quick",
            new_chat=True,
            answer_timeout_seconds=90,
        )

        quick_path = write_result_json(
            quick_result,
            output_dir / "quick.json",
        )

        print(
            "[PASS] Quick"
        )

        print(
            "[QUICK ANSWER LENGTH]",
            len(quick_result.answer),
        )

        print(
            "[QUICK SEARCH QUERIES]",
            len(
                quick_result.search_queries
            ),
        )

        print(
            "[QUICK SOURCES]",
            len(
                quick_result.sources
            ),
        )

        print(
            "[QUICK OUTPUT]",
            quick_path,
        )

        print()

        # 两种模式之间不要连续操作太快
        page.wait_for_timeout(
            8000
        )

        # =====================================
        # Research
        # =====================================

        print(
            "[RUN] Research"
        )

        research_result = runner.ask(
            RESEARCH_QUESTION,
            mode="research",
            new_chat=True,
            answer_timeout_seconds=240,
        )

        research_path = write_result_json(
            research_result,
            output_dir / "research.json",
        )

        print(
            "[PASS] Research"
        )

        print(
            "[RESEARCH ANSWER LENGTH]",
            len(
                research_result.answer
            ),
        )

        print(
            "[RESEARCH SEARCH QUERIES]",
            len(
                research_result.search_queries
            ),
        )

        print(
            "[RESEARCH SOURCES]",
            len(
                research_result.sources
            ),
        )

        print(
            "[CITATION MAPPING]",
            research_result
            .citation_mapping_available,
        )

        print(
            "[RESEARCH OUTPUT]",
            research_path,
        )

        print()

        print(
            "[PASS] real result smoke completed"
        )

        print(
            "[OUTPUT DIR]",
            output_dir,
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()
