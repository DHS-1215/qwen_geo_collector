from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT_DIR / "output"
PROFILE_DIR = ROOT_DIR / ".qwen_profile"

QWEN_URL = "https://www.qianwen.com/?ch=tongyi_redirect"


INPUT_SELECTOR = (
    '[role="textbox"]'
    '[data-slate-editor="true"]'
    '[contenteditable="true"]'
)

SEND_BUTTON_SELECTOR = (
    'button[aria-label="发送消息"]'
)

MODE_BUTTON_SELECTOR = (
    'button[aria-label="快速"]'
    '[aria-haspopup="menu"]'
)


def save_json(path: Path, data) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def first_visible(locator: Locator) -> Locator | None:
    for index in range(locator.count()):
        item = locator.nth(index)

        if item.is_visible():
            return item

    return None


def describe_locator(
    locator: Locator,
) -> dict:
    return {
        "count": locator.count(),
        "items": [
            {
                "index": i,
                "visible": locator.nth(i).is_visible(),
                "text": locator.nth(i).inner_text()
                if locator.nth(i).is_visible()
                else None,
                "outer_html": locator.nth(i).evaluate(
                    "el => el.outerHTML"
                ),
            }
            for i in range(locator.count())
        ],
    }


def collect_visible_controls(
    page: Page,
) -> list[dict]:
    return page.locator(
        """
        button,
        [role="menu"],
        [role="menuitem"],
        [role="option"],
        [role="dialog"],
        [role="listbox"]
        """
    ).evaluate_all(
        """
        elements => elements
            .map((el, index) => {
                const rect =
                    el.getBoundingClientRect();

                const style =
                    window.getComputedStyle(el);

                const visible =
                    rect.width > 0 &&
                    rect.height > 0 &&
                    style.display !== "none" &&
                    style.visibility !== "hidden";

                return {
                    index,
                    tag: el.tagName,
                    role: el.getAttribute("role"),
                    aria_label:
                        el.getAttribute("aria-label"),
                    aria_pressed:
                        el.getAttribute("aria-pressed"),
                    aria_checked:
                        el.getAttribute("aria-checked"),
                    aria_expanded:
                        el.getAttribute("aria-expanded"),
                    data_state:
                        el.getAttribute("data-state"),
                    text:
                        (
                            el.innerText ||
                            el.textContent ||
                            ""
                        ).trim(),
                    visible,
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                };
            })
            .filter(item => item.visible)
        """
    )


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
        OUTPUT_DIR
        / f"qwen_control_investigation_{timestamp}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as playwright:

        context = (
            playwright.chromium
            .launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                channel="chrome",
                headless=False,
                viewport={
                    "width": 1440,
                    "height": 1000,
                },
            )
        )

        page = (
            context.pages[0]
            if context.pages
            else context.new_page()
        )

        print(f"[OPEN] {QWEN_URL}")

        page.goto(
            QWEN_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.wait_for_timeout(5000)

        # ========================================
        # 1. 输入框调查
        # ========================================

        input_locator = page.locator(
            INPUT_SELECTOR
        )

        send_locator = page.locator(
            SEND_BUTTON_SELECTOR
        )

        mode_locator = page.locator(
            MODE_BUTTON_SELECTOR
        )

        save_json(
            output_dir / "01_core_controls.json",
            {
                "url": page.url,
                "input": describe_locator(
                    input_locator
                ),
                "send": describe_locator(
                    send_locator
                ),
                "mode": describe_locator(
                    mode_locator
                ),
            },
        )

        input_box = first_visible(
            input_locator
        )

        send_button = first_visible(
            send_locator
        )

        if input_box is None:
            raise RuntimeError(
                "没有找到可见输入框"
            )

        if send_button is None:
            raise RuntimeError(
                "没有找到可见发送按钮"
            )

        print("[PASS] input located")
        print("[PASS] send button located")

        print(
            "[STATE] send disabled before:",
            send_button.is_disabled(),
        )

        # ========================================
        # 2. 测试输入，但绝不发送
        # ========================================

        test_text = (
            "QWEN_GEO_CONTROL_TEST"
        )

        input_box.fill(test_text)

        page.wait_for_timeout(1000)

        print(
            "[STATE] send disabled after input:",
            send_button.is_disabled(),
        )

        page.screenshot(
            path=str(
                output_dir /
                "02_after_test_input.png"
            ),
            full_page=True,
        )

        save_json(
            output_dir /
            "02_after_test_input.json",
            {
                "input_text":
                    input_box.inner_text(),
                "send_disabled":
                    send_button.is_disabled(),
                "send_html":
                    send_button.evaluate(
                        "el => el.outerHTML"
                    ),
            },
        )

        # 清空，不发送
        input_box.fill("")

        page.wait_for_timeout(500)

        print("[PASS] input cleared")

        # ========================================
        # 3. 调查“快速”菜单
        # ========================================

        mode_button = first_visible(
            mode_locator
        )

        if mode_button is None:
            raise RuntimeError(
                "没有找到可见模式按钮"
            )

        print("[CLICK] mode button")

        mode_button.click()

        # 千问可能存在动画 / 异步渲染
        for delay in (
            100,
            300,
            800,
            1500,
        ):
            page.wait_for_timeout(delay)

            save_json(
                output_dir /
                f"03_mode_menu_{delay}ms.json",
                collect_visible_controls(
                    page
                ),
            )

            page.screenshot(
                path=str(
                    output_dir /
                    f"03_mode_menu_{delay}ms.png"
                ),
                full_page=True,
            )

        print()
        print(
            "[PASS] control investigation completed"
        )
        print(
            f"[OUTPUT] {output_dir}"
        )

        input(
            "观察模式菜单后按 Enter 关闭浏览器..."
        )

        context.close()


if __name__ == "__main__":
    main()