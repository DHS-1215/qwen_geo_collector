from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.qwen.browser import QwenBrowserSession
from app.qwen.runner import QwenRunner
from app.qwen.selectors import (
    ANSWER_WRAP_SELECTOR,
    RESEARCH_WORKFLOW_SELECTOR,
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


def collect_workflow_nodes(
    workflow,
) -> list[dict]:
    return workflow.locator("*").evaluate_all(
        """
        elements => elements.map((el, index) => {
            const rect = el.getBoundingClientRect();

            const text = (
                el.innerText ||
                el.textContent ||
                ""
            ).trim();

            const attrs = {};

            for (const attr of el.attributes) {
                if (
                    attr.name.startsWith("data-") ||
                    attr.name.startsWith("aria-") ||
                    attr.name === "role"
                ) {
                    attrs[attr.name] = attr.value;
                }
            }

            const parent = el.parentElement;

            const grandparent =
                parent?.parentElement || null;

            return {
                index,

                tag:
                    el.tagName,

                text:
                    text.slice(0, 2000),

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

                x:
                    rect.x,

                y:
                    rect.y,

                width:
                    rect.width,

                height:
                    rect.height,

                child_element_count:
                    el.children.length,

                parent: parent
                    ? {
                        tag:
                            parent.tagName,

                        class_name:
                            typeof parent.className
                                === "string"
                                ? parent.className
                                : null,

                        text:
                            (
                                parent.innerText ||
                                parent.textContent ||
                                ""
                            )
                            .trim()
                            .slice(0, 2000)
                    }
                    : null,

                grandparent: grandparent
                    ? {
                        tag:
                            grandparent.tagName,

                        class_name:
                            typeof grandparent.className
                                === "string"
                                ? grandparent.className
                                : null,

                        text:
                            (
                                grandparent.innerText ||
                                grandparent.textContent ||
                                ""
                            )
                            .trim()
                            .slice(0, 2000)
                    }
                    : null,

                outer_html:
                    el.outerHTML.slice(
                        0,
                        8000
                    )
            };
        }).filter(item => {
            if (!item.text) {
                return false;
            }

            return true;
        })
        """
    )


def collect_leaf_text_nodes(
    workflow,
) -> list[dict]:
    """
    重点找叶子文本节点。

    搜索关键词通常最终会落在某个 span/div
    里面，而且自身没有太多子元素。
    """

    return workflow.locator("*").evaluate_all(
        """
        elements => elements
            .map((el, index) => {
                const rect =
                    el.getBoundingClientRect();

                const text =
                    (
                        el.innerText ||
                        el.textContent ||
                        ""
                    ).trim();

                const elementChildren =
                    Array.from(el.children);

                const hasChildWithSameText =
                    elementChildren.some(child => {
                        const childText =
                            (
                                child.innerText ||
                                child.textContent ||
                                ""
                            ).trim();

                        return childText === text;
                    });

                const attrs = {};

                for (
                    const attr of el.attributes
                ) {
                    if (
                        attr.name.startsWith("data-") ||
                        attr.name.startsWith("aria-") ||
                        attr.name === "role"
                    ) {
                        attrs[attr.name] =
                            attr.value;
                    }
                }

                return {
                    index,

                    tag:
                        el.tagName,

                    text,

                    class_name:
                        typeof el.className
                            === "string"
                            ? el.className
                            : null,

                    attrs,

                    visible:
                        rect.width > 0 &&
                        rect.height > 0,

                    child_element_count:
                        el.children.length,

                    has_child_with_same_text:
                        hasChildWithSameText,

                    parent_html:
                        el.parentElement
                            ? el.parentElement
                                .outerHTML
                                .slice(
                                    0,
                                    10000
                                )
                            : null,

                    outer_html:
                        el.outerHTML.slice(
                            0,
                            6000
                        )
                };
            })
            .filter(item => {

                if (!item.text) {
                    return false;
                }

                if (!item.visible) {
                    return false;
                }

                if (
                    item.has_child_with_same_text
                ) {
                    return false;
                }

                /*
                 * 暂时保留长度不大的文本。
                 * 搜索 query 一般不会特别长。
                 */
                if (
                    item.text.length > 200
                ) {
                    return false;
                }

                return true;
            });
        """
    )


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
        OUTPUT_DIR /
        f"qwen_search_query_dom_{timestamp}"
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

        runner.ensure_no_risk_control()

        answers = page.locator(
            ANSWER_WRAP_SELECTOR
        )

        if answers.count() == 0:
            raise RuntimeError(
                "当前千问页面没有回答"
            )

        answer_wrap = (
            answers.last
        )

        workflow = (
            answer_wrap.locator(
                RESEARCH_WORKFLOW_SELECTOR
            )
        )

        print(
            "[WORKFLOW COUNT]",
            workflow.count(),
        )

        if workflow.count() == 0:
            raise RuntimeError(
                "当前最后一轮回答没有 "
                "Research workflow"
            )

        workflow = workflow.first

        # =====================================
        # 原始证据
        # =====================================

        page.screenshot(
            path=str(
                output_dir /
                "page.png"
            ),
            full_page=True,
        )

        (
            output_dir /
            "workflow.html"
        ).write_text(
            workflow.evaluate(
                "el => el.outerHTML"
            ),
            encoding="utf-8",
        )

        (
            output_dir /
            "workflow_text.txt"
        ).write_text(
            workflow.inner_text(),
            encoding="utf-8",
        )

        # =====================================
        # 全量工作流节点
        # =====================================

        workflow_nodes = (
            collect_workflow_nodes(
                workflow
            )
        )

        save_json(
            output_dir /
            "workflow_nodes.json",
            workflow_nodes,
        )

        # =====================================
        # 叶子文本节点
        # =====================================

        leaf_nodes = (
            collect_leaf_text_nodes(
                workflow
            )
        )

        save_json(
            output_dir /
            "leaf_text_nodes.json",
            leaf_nodes,
        )

        print(
            "[WORKFLOW NODES]",
            len(workflow_nodes),
        )

        print(
            "[LEAF TEXT NODES]",
            len(leaf_nodes),
        )

        print()
        print(
            "[LEAF TEXT PREVIEW]"
        )

        for item in leaf_nodes:
            text = item["text"]

            if (
                len(text) >= 4
                and text not in {
                    "查看全部",
                    "思考研究",
                    "搜索",
                    "参考资料",
                }
            ):
                print(
                    "-",
                    repr(text),
                )

        print()
        print(
            "[PASS] search query DOM captured"
        )

        print(
            "[OUTPUT]",
            output_dir,
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()