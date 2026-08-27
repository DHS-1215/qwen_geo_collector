from __future__ import annotations

import time

from playwright.sync_api import Locator, Page, sync_playwright

CDP_URL = "http://127.0.0.1:9222"

QUESTION_WRAP_SELECTOR = "[data-chat-question-wrap]"
ANSWER_WRAP_SELECTOR = "[data-chat-answers-wrap]"


def first_visible(
        locator: Locator,
) -> Locator | None:
    for index in range(locator.count()):
        item = locator.nth(index)

        try:
            if item.is_visible():
                return item
        except Exception:
            continue

    return None


def get_qwen_page(context) -> Page:
    for page in context.pages:
        if "qianwen.com" in page.url:
            return page

    raise RuntimeError(
        "没有找到千问页面"
    )


def detect_risk_control(
        page: Page,
) -> bool:
    body_text = (
        page.locator("body")
        .inner_text()
    )

    risk_texts = (
        "请拖动下方滑块完成验证",
        "通过验证以确保正常访问",
        "验证失败",
    )

    return any(
        text in body_text
        for text in risk_texts
    )


def find_new_chat_button(
        page: Page,
) -> Locator | None:
    # 第一优先：文本
    locator = page.get_by_text(
        "新建对话",
        exact=True,
    )

    button = first_visible(locator)

    if button is not None:
        return button

    # 第二优先：包含该文本的按钮
    locator = page.locator("button")

    for index in range(locator.count()):
        item = locator.nth(index)

        try:
            if not item.is_visible():
                continue

            text = (
                item.inner_text()
                .strip()
            )

            if "新建对话" in text:
                return item

        except Exception:
            continue

    return None


def wait_for_new_chat(
        page: Page,
        old_url: str,
        timeout_seconds: int = 10,
) -> None:
    start = time.monotonic()

    while (
            time.monotonic() - start
            < timeout_seconds
    ):
        if detect_risk_control(page):
            raise RuntimeError(
                "RISK_CONTROL"
            )

        question_count = (
            page.locator(
                QUESTION_WRAP_SELECTOR
            ).count()
        )

        answer_count = (
            page.locator(
                ANSWER_WRAP_SELECTOR
            ).count()
        )

        current_url = page.url

        # 新聊天一般会回到首页/新会话状态，
        # 核心判断仍以问答节点清空为准。
        if (
                question_count == 0
                and answer_count == 0
        ):
            print(
                "[PASS] empty conversation detected"
            )
            print(
                "[URL]",
                current_url,
            )

            if current_url != old_url:
                print(
                    "[PASS] URL changed"
                )

            return

        page.wait_for_timeout(200)

    raise RuntimeError(
        "等待新建对话完成超时"
    )


def main() -> None:
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
            "[PASS] Qwen connected"
        )

        if detect_risk_control(page):
            raise RuntimeError(
                "当前页面处于风控状态"
            )

        old_url = page.url

        old_questions = (
            page.locator(
                QUESTION_WRAP_SELECTOR
            ).count()
        )

        old_answers = (
            page.locator(
                ANSWER_WRAP_SELECTOR
            ).count()
        )

        print(
            "[BEFORE] URL:",
            old_url,
        )

        print(
            "[BEFORE] questions:",
            old_questions,
        )

        print(
            "[BEFORE] answers:",
            old_answers,
        )

        new_chat_button = (
            find_new_chat_button(page)
        )

        if new_chat_button is None:
            raise RuntimeError(
                "没有找到新建对话按钮"
            )

        print(
            "[CLICK] 新建对话"
        )

        new_chat_button.click()

        wait_for_new_chat(
            page,
            old_url,
            timeout_seconds=10,
        )

        print(
            "[AFTER] questions:",
            page.locator(
                QUESTION_WRAP_SELECTOR
            ).count(),
        )

        print(
            "[AFTER] answers:",
            page.locator(
                ANSWER_WRAP_SELECTOR
            ).count(),
        )

        print(
            "[RISK]",
            detect_risk_control(page),
        )

        print()
        print(
            "[PASS] new chat investigation completed"
        )


if __name__ == "__main__":
    main()
