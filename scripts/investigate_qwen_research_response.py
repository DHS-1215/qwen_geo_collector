from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.qwen.browser import QwenBrowserSession
from app.qwen.runner import QwenRunner

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output"

QUESTION = (
    "鸿茅药酒到底是药还是酒？"
    "请基于公开网页资料回答，并附参考来源。"
)


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


def collect_links(page) -> list[dict]:
    return page.locator("a").evaluate_all(
        """
        elements => elements.map((el, index) => ({
            index,

            text:
                (
                    el.innerText ||
                    el.textContent ||
                    ""
                )
                .trim()
                .slice(0, 1000),

            href:
                el.href || null,

            title:
                el.getAttribute("title"),

            aria_label:
                el.getAttribute("aria-label"),

            target:
                el.getAttribute("target"),

            class_name:
                typeof el.className === "string"
                    ? el.className
                    : null,

            visible:
                el.getBoundingClientRect().width > 0 &&
                el.getBoundingClientRect().height > 0
        }))
        """
    )


def collect_interesting_nodes(
        page,
) -> list[dict]:
    return page.locator("body *").evaluate_all(
        """
        elements => {
            const keywords = [
                "source",
                "reference",
                "citation",
                "cite",
                "search",
                "answer",
                "markdown",
                "来源",
                "参考",
                "引用",
                "搜索",
                "网页",
                "深度搜索",
                "深度研究"
            ];

            return elements
                .map((el, index) => {
                    const rect =
                        el.getBoundingClientRect();

                    const text =
                        (
                            el.innerText ||
                            el.textContent ||
                            ""
                        )
                        .trim();

                    const className =
                        typeof el.className === "string"
                            ? el.className
                            : "";

                    const attrs = {};

                    for (
                        const attr of el.attributes
                    ) {
                        if (
                            attr.name.startsWith("data-") ||
                            attr.name === "role" ||
                            attr.name.startsWith("aria-")
                        ) {
                            attrs[attr.name] =
                                attr.value;
                        }
                    }

                    const searchText = (
                        className +
                        " " +
                        text +
                        " " +
                        JSON.stringify(attrs)
                    ).toLowerCase();

                    const interesting =
                        keywords.some(
                            keyword =>
                                searchText.includes(
                                    keyword.toLowerCase()
                                )
                        );

                    return {
                        index,

                        interesting,

                        tag:
                            el.tagName,

                        text:
                            text.slice(0, 3000),

                        id:
                            el.id || null,

                        class_name:
                            className || null,

                        attrs,

                        x:
                            rect.x,

                        y:
                            rect.y,

                        width:
                            rect.width,

                        height:
                            rect.height,

                        visible:
                            rect.width > 0 &&
                            rect.height > 0
                    };
                })
                .filter(
                    item =>
                        item.interesting
                );
        }
        """
    )


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
            OUTPUT_DIR /
            f"qwen_research_{timestamp}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    session = QwenBrowserSession()

    try:
        page = session.connect()

        print(
            "[PASS] browser connected"
        )

        runner = QwenRunner(
            page
        )

        print(
            "[MODE] before:",
            runner.get_mode(),
        )

        print(
            "[ASK]",
            QUESTION,
        )

        result = runner.ask(
            QUESTION,
            mode="research",
            new_chat=True,
            answer_timeout_seconds=240,
        )

        print()
        print(
            "[PASS] research answer completed"
        )

        print(
            "[MODE]",
            result.mode,
        )

        print(
            "[MODE LABEL]",
            result.mode_label,
        )

        print(
            "[TURN]",
            result.turn_id,
        )

        print(
            "[QUESTION]",
            result.question,
        )

        print()
        print(
            "[ANSWER]"
        )
        print(
            result.answer
        )

        print()
        print(
            "[URL]",
            result.chat_url,
        )

        # =====================================
        # 全页面证据
        # =====================================

        page.screenshot(
            path=str(
                output_dir /
                "research_final.png"
            ),
            full_page=True,
        )

        (
                output_dir /
                "research_final.html"
        ).write_text(
            page.content(),
            encoding="utf-8",
        )

        (
                output_dir /
                "body_text.txt"
        ).write_text(
            page.locator(
                "body"
            ).inner_text(),
            encoding="utf-8",
        )

        # =====================================
        # 当前回答轮次
        # =====================================

        answer_wrap = page.locator(
            f'[data-chat-answers-wrap="'
            f'{result.turn_id}"]'
        )

        if answer_wrap.count() > 0:
            (
                    output_dir /
                    "answer_wrap.html"
            ).write_text(
                answer_wrap
                .first
                .evaluate(
                    "el => el.outerHTML"
                ),
                encoding="utf-8",
            )

        question_wrap = page.locator(
            f'[data-chat-question-wrap="'
            f'{result.turn_id}"]'
        )

        if question_wrap.count() > 0:
            (
                    output_dir /
                    "question_wrap.html"
            ).write_text(
                question_wrap
                .first
                .evaluate(
                    "el => el.outerHTML"
                ),
                encoding="utf-8",
            )

        # =====================================
        # URL / 来源候选
        # =====================================

        save_json(
            output_dir /
            "links.json",
            collect_links(page),
        )

        save_json(
            output_dir /
            "interesting_nodes.json",
            collect_interesting_nodes(
                page
            ),
        )

        save_json(
            output_dir /
            "result.json",
            result.model_dump(
                mode="json"
            ),
        )

        print()
        print(
            "[PASS] research investigation captured"
        )

        print(
            "[OUTPUT]",
            output_dir,
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()
