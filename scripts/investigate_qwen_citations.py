from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.qwen.browser import QwenBrowserSession
from app.qwen.runner import QwenRunner
from app.qwen.selectors import (
    ANSWER_FINAL_SELECTOR,
    ANSWER_WRAP_SELECTOR,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output"


def save_json(
        path: Path,
        data,
) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def collect_final_answer_nodes(
        final_answer,
) -> list[dict]:
    return final_answer.locator("*").evaluate_all(
        """
        elements => elements.map((el, index) => {
            const rect = el.getBoundingClientRect();

            const attrs = {};

            for (const attr of el.attributes) {
                if (
                    attr.name.startsWith("data-") ||
                    attr.name.startsWith("aria-") ||
                    attr.name === "role" ||
                    attr.name === "href"
                ) {
                    attrs[attr.name] = attr.value;
                }
            }

            return {
                index,

                tag:
                    el.tagName,

                text:
                    (
                        el.innerText ||
                        el.textContent ||
                        ""
                    )
                    .trim()
                    .slice(0, 2000),

                id:
                    el.id || null,

                class_name:
                    typeof el.className === "string"
                        ? el.className
                        : null,

                attrs,

                visible:
                    rect.width > 0 &&
                    rect.height > 0,

                child_count:
                    el.children.length,

                outer_html:
                    el.outerHTML.slice(
                        0,
                        12000
                    )
            };
        })
        """
    )


def collect_possible_citations(
        final_answer,
) -> list[dict]:
    return final_answer.locator(
        """
        a,
        sup,
        cite,
        button,
        [role="button"],
        [class*="cite"],
        [class*="citation"],
        [class*="reference"],
        [class*="source"],
        [data-citation],
        [data-source],
        [data-reference]
        """
    ).evaluate_all(
        """
        elements => elements.map((el, index) => {
            const attrs = {};

            for (const attr of el.attributes) {
                attrs[attr.name] = attr.value;
            }

            return {
                index,

                tag:
                    el.tagName,

                text:
                    (
                        el.innerText ||
                        el.textContent ||
                        ""
                    ).trim(),

                attrs,

                class_name:
                    typeof el.className === "string"
                        ? el.className
                        : null,

                outer_html:
                    el.outerHTML.slice(
                        0,
                        12000
                    )
            };
        })
        """
    )


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
            OUTPUT_DIR /
            f"qwen_citation_dom_{timestamp}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    session = QwenBrowserSession()

    try:
        page = session.connect()

        runner = QwenRunner(page)

        runner.ensure_no_risk_control()

        answers = page.locator(
            ANSWER_WRAP_SELECTOR
        )

        if answers.count() == 0:
            raise RuntimeError(
                "当前页面没有回答"
            )

        answer_wrap = answers.last

        final_answer = (
            answer_wrap.locator(
                ANSWER_FINAL_SELECTOR
            ).last
        )

        if final_answer.count() == 0:
            raise RuntimeError(
                "没有找到最终回答正文"
            )

        print(
            "[ANSWER LENGTH]",
            len(
                final_answer
                .inner_text()
                .strip()
            ),
        )

        # -------------------------
        # 原始 HTML
        # -------------------------

        (
                output_dir /
                "final_answer.html"
        ).write_text(
            final_answer.evaluate(
                "el => el.outerHTML"
            ),
            encoding="utf-8",
        )

        # -------------------------
        # 回答全部子节点
        # -------------------------

        nodes = collect_final_answer_nodes(
            final_answer
        )

        save_json(
            output_dir /
            "final_answer_nodes.json",
            nodes,
        )

        # -------------------------
        # 疑似 citation
        # -------------------------

        candidates = (
            collect_possible_citations(
                final_answer
            )
        )

        save_json(
            output_dir /
            "citation_candidates.json",
            candidates,
        )

        print(
            "[ALL NODES]",
            len(nodes),
        )

        print(
            "[CITATION CANDIDATES]",
            len(candidates),
        )

        print()

        for item in candidates:
            print(
                "[CANDIDATE]",
                item["tag"],
                repr(item["text"]),
                item["attrs"],
            )

        print()
        print(
            "[PASS] citation DOM captured"
        )

        print(
            "[OUTPUT]",
            output_dir,
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()
