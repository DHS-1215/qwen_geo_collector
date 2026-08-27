from __future__ import annotations

from pathlib import Path

from app.qwen.models import (
    QwenAnswerResult,
    QwenSource,
)
from app.qwen.serialization import (
    write_result_json,
)

ROOT_DIR = Path(
    __file__
).resolve().parents[1]


def main() -> None:
    output_dir = (
            ROOT_DIR /
            "output" /
            "schema_smoke"
    )

    # =====================================
    # Quick
    # =====================================

    quick_result = QwenAnswerResult(
        question="测试 Quick",
        answer="Quick answer",
        turn_id="quick_turn_test",
        chat_url=(
            "https://www.qianwen.com/chat/test"
        ),
        mode="quick",
        mode_label="快速",
    )

    quick_path = write_result_json(
        quick_result,
        output_dir /
        "quick_result.json",
    )

    # =====================================
    # Research
    # =====================================

    research_result = QwenAnswerResult(
        question="测试 Research",
        answer="Research answer",
        turn_id="research_turn_test",
        chat_url=(
            "https://www.qianwen.com/chat/test"
        ),
        mode="research",
        mode_label="思考研究",
        search_queries=[
            "测试关键词 1",
            "测试关键词 2",
        ],
        sources=[
            QwenSource(
                rank=1,
                title="测试来源",
                url="https://example.com",
            )
        ],
    )

    research_path = write_result_json(
        research_result,
        output_dir /
        "research_result.json",
    )

    print(
        "[PASS] result schema smoke"
    )

    print(
        "[QUICK]",
        quick_path,
    )

    print(
        "[RESEARCH]",
        research_path,
    )

    print()
    print(
        "[QUICK SOURCES]",
        len(quick_result.sources),
    )

    print(
        "[QUICK SEARCH QUERIES]",
        len(
            quick_result.search_queries
        ),
    )

    print(
        "[RESEARCH SOURCES]",
        len(
            research_result.sources
        ),
    )

    print(
        "[RESEARCH SEARCH QUERIES]",
        len(
            research_result.search_queries
        ),
    )

    print(
        "[CITATION MAPPING AVAILABLE]",
        research_result
        .citation_mapping_available,
    )


if __name__ == "__main__":
    main()
