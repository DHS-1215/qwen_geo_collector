from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT_DIR / "output"

CDP_URL = "http://127.0.0.1:9222"


def save_json(path: Path, data) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def get_qwen_page(context) -> Page:
    for page in context.pages:
        if "qianwen.com" in page.url:
            return page

    raise RuntimeError(
        "没有找到千问页面"
    )


def collect_all_candidates(
    page: Page,
) -> list[dict]:

    return page.locator(
        """
        button,
        a,
        article,
        main,
        p,
        div,
        span,
        [role],
        [data-testid],
        [data-message-id],
        [data-role],
        [data-content],
        [data-index]
        """
    ).evaluate_all(
        """
        elements => elements.map((el, index) => {

            const rect =
                el.getBoundingClientRect();

            const style =
                window.getComputedStyle(el);

            const visible =
                rect.width > 0 &&
                rect.height > 0 &&
                style.display !== "none" &&
                style.visibility !== "hidden";

            const text =
                (
                    el.innerText ||
                    el.textContent ||
                    ""
                )
                .trim();

            return {
                index,

                tag:
                    el.tagName,

                visible,

                text:
                    text.slice(0, 3000),

                id:
                    el.id || null,

                class_name:
                    typeof el.className === "string"
                        ? el.className
                        : null,

                role:
                    el.getAttribute("role"),

                aria_label:
                    el.getAttribute(
                        "aria-label"
                    ),

                data_testid:
                    el.getAttribute(
                        "data-testid"
                    ),

                data_message_id:
                    el.getAttribute(
                        "data-message-id"
                    ),

                data_role:
                    el.getAttribute(
                        "data-role"
                    ),

                data_content:
                    el.getAttribute(
                        "data-content"
                    ),

                x:
                    rect.x,

                y:
                    rect.y,

                width:
                    rect.width,

                height:
                    rect.height
            };

        }).filter(item => {

            if (!item.visible) {
                return false;
            }

            if (!item.text) {
                return false;
            }

            return true;
        })
        """
    )


def collect_matching_text_nodes(
    page: Page,
    needle: str,
) -> list[dict]:

    return page.locator(
        "body *"
    ).evaluate_all(
        """
        (elements, needle) => elements
            .filter(el => {
                const text =
                    (
                        el.innerText ||
                        el.textContent ||
                        ""
                    ).trim();

                return text.includes(
                    needle
                );
            })
            .map((el, index) => {

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
                        .slice(0, 3000),

                    id:
                        el.id || null,

                    class_name:
                        typeof el.className === "string"
                            ? el.className
                            : null,

                    role:
                        el.getAttribute(
                            "role"
                        ),

                    aria_label:
                        el.getAttribute(
                            "aria-label"
                        ),

                    data_testid:
                        el.getAttribute(
                            "data-testid"
                        ),

                    data_message_id:
                        el.getAttribute(
                            "data-message-id"
                        ),

                    outer_html:
                        el.outerHTML.slice(
                            0,
                            10000
                        ),

                    x:
                        rect.x,

                    y:
                        rect.y,

                    width:
                        rect.width,

                    height:
                        rect.height
                };
            })
        """,
        needle,
    )


def main() -> None:

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
        OUTPUT_DIR /
        f"qwen_response_dom_{timestamp}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as playwright:

        print(
            f"[CONNECT] {CDP_URL}"
        )

        browser = (
            playwright.chromium
            .connect_over_cdp(
                CDP_URL
            )
        )

        if not browser.contexts:
            raise RuntimeError(
                "没有 browser context"
            )

        context = browser.contexts[0]

        page = get_qwen_page(
            context
        )

        print(
            "[PASS] Qwen page connected"
        )

        print(
            "[URL]",
            page.url,
        )

        body_text = (
            page.locator("body")
            .inner_text()
        )

        print(
            "[BODY LENGTH]",
            len(body_text),
        )

        print(
            "[ANSWER FOUND]",
            "QWEN_GEO_CDP_PROBE_OK"
            in body_text,
        )

        # -------------------------
        # 完整证据
        # -------------------------

        page.screenshot(
            path=str(
                output_dir /
                "current_response.png"
            ),
            full_page=True,
        )

        (
            output_dir /
            "current_response.html"
        ).write_text(
            page.content(),
            encoding="utf-8",
        )

        (
            output_dir /
            "body_text.txt"
        ).write_text(
            body_text,
            encoding="utf-8",
        )

        # -------------------------
        # 广义候选节点
        # -------------------------

        save_json(
            output_dir /
            "all_candidates.json",
            collect_all_candidates(
                page
            ),
        )

        # -------------------------
        # 用户问题 DOM
        # -------------------------

        save_json(
            output_dir /
            "question_matches.json",
            collect_matching_text_nodes(
                page,
                "请只回答：QWEN_GEO_CDP_PROBE_OK",
            ),
        )

        # -------------------------
        # AI 回答 DOM
        # -------------------------

        save_json(
            output_dir /
            "answer_matches.json",
            collect_matching_text_nodes(
                page,
                "QWEN_GEO_CDP_PROBE_OK",
            ),
        )

        print()
        print(
            "[PASS] response DOM captured"
        )

        print(
            "[OUTPUT]",
            output_dir,
        )


if __name__ == "__main__":
    main()