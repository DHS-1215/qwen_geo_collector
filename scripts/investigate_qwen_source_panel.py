from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.qwen.browser import QwenBrowserSession
from app.qwen.runner import QwenRunner

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output"


def save_json(path: Path, data) -> None:
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
                ).trim(),

            href:
                el.href || null,

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


def capture(
        page,
        output_dir: Path,
        name: str,
) -> None:
    print(
        "[CAPTURE]",
        name,
    )

    page.screenshot(
        path=str(
            output_dir /
            f"{name}.png"
        ),
        full_page=True,
    )

    (
            output_dir /
            f"{name}.html"
    ).write_text(
        page.content(),
        encoding="utf-8",
    )

    (
            output_dir /
            f"{name}_body.txt"
    ).write_text(
        page.locator(
            "body"
        ).inner_text(),
        encoding="utf-8",
    )

    save_json(
        output_dir /
        f"{name}_links.json",
        collect_links(page),
    )


def collect_dialog_nodes(
        page,
) -> list[dict]:
    return page.locator(
        """
        [role="dialog"],
        [role="presentation"],
        [data-radix-portal],
        [class*="drawer"],
        [class*="dialog"],
        [class*="modal"],
        [class*="source"],
        [class*="reference"]
        """
    ).evaluate_all(
        """
        elements => elements.map((el, index) => {
            const rect =
                el.getBoundingClientRect();

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
                    .slice(0, 5000),

                id:
                    el.id || null,

                role:
                    el.getAttribute("role"),

                class_name:
                    typeof el.className === "string"
                        ? el.className
                        : null,

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

                outer_html:
                    el.outerHTML.slice(
                        0,
                        15000
                    )
            };
        })
        """
    )


def first_visible(locator):
    for index in range(
            locator.count()
    ):
        item = locator.nth(index)

        try:
            if item.is_visible():
                return item
        except Exception:
            continue

    return None


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
            OUTPUT_DIR /
            f"qwen_source_panel_{timestamp}"
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
            "[data-chat-answers-wrap]"
        )

        if answers.count() == 0:
            raise RuntimeError(
                "当前页面没有回答"
            )

        answer_wrap = answers.last

        capture(
            page,
            output_dir,
            "01_before",
        )

        # ==================================
        # 搜索步骤中的“查看全部”
        # ==================================

        workflow = answer_wrap.locator(
            '[data-card_name="bar_workflow"]'
        )

        if workflow.count() == 0:
            raise RuntimeError(
                "当前回答没有 Research workflow"
            )

        view_all = first_visible(
            workflow.get_by_text(
                "查看全部",
                exact=True,
            )
        )

        if view_all is None:
            raise RuntimeError(
                "没有找到可见的“查看全部”"
            )

        print(
            "[CLICK] 查看全部"
        )

        try:
            view_all.click(
                timeout=3000
            )

            print(
                "[CLICK] normal click success"
            )

        except Exception as exc:
            print(
                "[WARN] normal click blocked:",
                type(exc).__name__,
            )

            print(
                "[CLICK] fallback to DOM click"
            )

            view_all.evaluate(
                "el => el.click()"
            )

        page.wait_for_timeout(
            1500
        )

        capture(
            page,
            output_dir,
            "02_after_view_all",
        )

        save_json(
            output_dir /
            "02_after_view_all_dialog_nodes.json",
            collect_dialog_nodes(
                page
            ),
        )

        print()
        print(
            "[LINK COUNT]",
            len(
                collect_links(page)
            ),
        )

        print(
            "[OUTPUT]",
            output_dir,
        )

        input(
            "观察来源面板后按 Enter 结束..."
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()
