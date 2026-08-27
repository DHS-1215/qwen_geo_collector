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

TEST_TEXT = "QWEN_GEO_CDP_FILL_TEST"


def first_visible(locator: Locator) -> Locator | None:
    for index in range(locator.count()):
        item = locator.nth(index)

        try:
            if item.is_visible():
                return item
        except Exception:
            continue

    return None


def detect_risk_control(page: Page) -> bool:
    body_text = page.locator("body").inner_text()

    risk_texts = (
        "请拖动下方滑块完成验证",
        "通过验证以确保正常访问",
        "验证失败",
    )

    return any(
        text in body_text
        for text in risk_texts
    )


def main() -> None:
    with sync_playwright() as playwright:
        print(f"[CONNECT] {CDP_URL}")

        browser = playwright.chromium.connect_over_cdp(
            CDP_URL
        )

        if not browser.contexts:
            raise RuntimeError(
                "没有找到 browser context"
            )

        context = browser.contexts[0]

        qwen_pages = [
            page
            for page in context.pages
            if "qianwen.com" in page.url
        ]

        if not qwen_pages:
            raise RuntimeError(
                "没有找到千问页面"
            )

        page = qwen_pages[0]

        print("[PASS] Qwen page connected")

        print(
            "[RISK] before:",
            detect_risk_control(page),
        )

        input_box = first_visible(
            page.locator(INPUT_SELECTOR)
        )

        send_button = first_visible(
            page.locator(
                SEND_BUTTON_SELECTOR
            )
        )

        if input_box is None:
            raise RuntimeError(
                "没有找到可见输入框"
            )

        if send_button is None:
            raise RuntimeError(
                "没有找到可见发送按钮"
            )

        print(
            "[STATE] send disabled before:",
            send_button.is_disabled(),
        )

        print("[FILL] test text")

        input_box.fill(
            TEST_TEXT
        )

        page.wait_for_timeout(2000)

        print(
            "[TEXT]",
            input_box.inner_text(),
        )

        print(
            "[STATE] send disabled after:",
            send_button.is_disabled(),
        )

        print(
            "[RISK] after fill:",
            detect_risk_control(page),
        )

        input(
            "请观察页面，确认没有验证码后按 Enter 清空..."
        )

        input_box.fill("")

        page.wait_for_timeout(500)

        print("[PASS] input cleared")

        print(
            "[RISK] final:",
            detect_risk_control(page),
        )

        # connect_over_cdp 不要关闭用户自己启动的 Chrome
        browser.close()


if __name__ == "__main__":
    main()
