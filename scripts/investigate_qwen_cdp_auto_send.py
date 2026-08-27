from __future__ import annotations

import time

from playwright.sync_api import Locator, Page, sync_playwright

CDP_URL = "http://127.0.0.1:9222"

INPUT_SELECTOR = (
    '[role="textbox"]'
    '[data-slate-editor="true"]'
    '[contenteditable="true"]'
)

SEND_BUTTON_SELECTOR = (
    'button[aria-label="发送消息"]'
)

QUESTION_WRAP_SELECTOR = (
    "[data-chat-question-wrap]"
)

ANSWER_WRAP_SELECTOR = (
    "[data-chat-answers-wrap]"
)

PROBE_TEXT = (
    "请只回答：QWEN_GEO_CDP_AUTO_SEND_OK"
)


def first_visible(
        locator: Locator,
) -> Locator | None:
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
    text = (
        page.locator("body")
        .inner_text()
    )

    risk_texts = (
        "请拖动下方滑块完成验证",
        "通过验证以确保正常访问",
        "验证失败",
    )

    return any(
        item in text
        for item in risk_texts
    )


def get_turn_ids(
        page: Page,
) -> set[str]:
    locator = page.locator(
        QUESTION_WRAP_SELECTOR
    )

    ids = set()

    for index in range(
            locator.count()
    ):
        value = (
            locator
            .nth(index)
            .get_attribute(
                "data-chat-question-wrap"
            )
        )

        if value:
            ids.add(value)

    return ids


def wait_for_new_turn(
        page: Page,
        previous_ids: set[str],
        timeout_seconds: int = 20,
) -> str:
    start = time.time()

    while (
            time.time() - start
            < timeout_seconds
    ):

        if detect_risk_control(page):
            raise RuntimeError(
                "RISK_CONTROL"
            )

        current_ids = get_turn_ids(
            page
        )

        new_ids = (
                current_ids -
                previous_ids
        )

        if new_ids:
            return next(
                iter(new_ids)
            )

        page.wait_for_timeout(
            200
        )

    raise RuntimeError(
        "等待新问题轮次超时"
    )


def wait_for_answer(
        page: Page,
        turn_id: str,
        timeout_seconds: int = 60,
) -> str:
    selector = (
        f'[data-chat-answers-wrap="{turn_id}"]'
    )

    answer_wrap = page.locator(
        selector
    )

    start = time.time()

    while (
            time.time() - start
            < timeout_seconds
    ):

        if detect_risk_control(page):
            raise RuntimeError(
                "RISK_CONTROL"
            )

        if answer_wrap.count() > 0:

            complete = (
                answer_wrap.locator(
                    ".qk-markdown-complete"
                )
            )

            feedback = (
                answer_wrap.locator(
                    '[data-answer-feedback-toolbar="true"]'
                )
            )

            if (
                    complete.count() > 0
                    and feedback.count() > 0
            ):
                text = (
                    complete
                    .first
                    .inner_text()
                    .strip()
                )

                if text:
                    return text

        page.wait_for_timeout(
            300
        )

    raise RuntimeError(
        "等待回答完成超时"
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

        context = (
            browser.contexts[0]
        )

        page = get_qwen_page(
            context
        )

        print(
            "[PASS] Qwen connected"
        )

        if detect_risk_control(page):
            raise RuntimeError(
                "页面当前已经处于风控状态"
            )

        input_box = first_visible(
            page.locator(
                INPUT_SELECTOR
            )
        )

        send_button = first_visible(
            page.locator(
                SEND_BUTTON_SELECTOR
            )
        )

        if input_box is None:
            raise RuntimeError(
                "没有找到输入框"
            )

        if send_button is None:
            raise RuntimeError(
                "没有找到发送按钮"
            )

        # -------------------------
        # 发送前记录已有轮次
        # -------------------------

        old_turn_ids = (
            get_turn_ids(page)
        )

        print(
            "[TURN] existing:",
            len(old_turn_ids),
        )

        # -------------------------
        # 填写
        # -------------------------

        input_box.fill(
            PROBE_TEXT
        )

        page.wait_for_timeout(
            500
        )

        print(
            "[FILL]",
            PROBE_TEXT,
        )

        print(
            "[SEND] disabled:",
            send_button.is_disabled(),
        )

        if send_button.is_disabled():
            raise RuntimeError(
                "发送按钮未激活"
            )

        # -------------------------
        # 自动点击
        # -------------------------

        print(
            "[CLICK] automatic send"
        )

        send_button.click()

        # -------------------------
        # 等真实新问题节点
        # -------------------------

        turn_id = wait_for_new_turn(
            page,
            old_turn_ids,
            timeout_seconds=20,
        )

        print(
            "[PASS] new turn:",
            turn_id,
        )

        question_wrap = (
            page.locator(
                f'[data-chat-question-wrap="{turn_id}"]'
            )
        )

        question_text = (
            question_wrap
            .locator(
                ".question-text-card"
            )
            .inner_text()
            .strip()
        )

        print(
            "[QUESTION]",
            question_text,
        )

        # -------------------------
        # 等回答
        # -------------------------

        print(
            "[WAIT] answer"
        )

        answer = wait_for_answer(
            page,
            turn_id,
            timeout_seconds=60,
        )

        print()
        print(
            "[PASS] answer completed"
        )

        print(
            "[ANSWER]",
            answer,
        )

        print(
            "[RISK]",
            detect_risk_control(page),
        )

        print(
            "[URL]",
            page.url,
        )


if __name__ == "__main__":
    main()
