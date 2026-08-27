from playwright.sync_api import sync_playwright


CDP_URL = "http://127.0.0.1:9222"


def main() -> None:
    with sync_playwright() as playwright:
        print(f"[CONNECT] {CDP_URL}")

        browser = playwright.chromium.connect_over_cdp(
            CDP_URL
        )

        contexts = browser.contexts

        print(
            "[INFO] contexts:",
            len(contexts),
        )

        if not contexts:
            raise RuntimeError(
                "没有找到 Chrome browser context"
            )

        context = contexts[0]

        print(
            "[INFO] pages:",
            len(context.pages),
        )

        for index, page in enumerate(
            context.pages
        ):
            print(
                f"[PAGE {index}]",
                page.url,
            )

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

        print(
            "[PASS] Qwen page connected"
        )

        print(
            "[TITLE]",
            page.title(),
        )

        print(
            "[URL]",
            page.url,
        )

        print(
            "[BODY LENGTH]",
            len(
                page.locator(
                    "body"
                ).inner_text()
            ),
        )

        input(
            "连接成功，按 Enter 退出..."
        )


if __name__ == "__main__":
    main()
