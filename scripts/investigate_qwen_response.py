from __future__ import annotations

import json
import time
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

PROBE_TEXT = "请只回答：QWEN_GEO_PROBE_OK"


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

        try:
            if item.is_visible():
                return item
        except Exception:
            continue

    return None


def find_mode_button(page: Page) -> Locator | None:
    locator = page.locator(
        'button[aria-haspopup="menu"]'
    )

    for index in range(locator.count()):
        item = locator.nth(index)

        try:
            if not item.is_visible():
                continue

            label = item.get_attribute(
                "aria-label"
            )

            if label in {
                "快速",
                "思考研究",
            }:
                return item

        except Exception:
            continue

    return None


def click_visible_text(
        page: Page,
        text: str,
) -> None:
    locator = page.get_by_text(
        text,
        exact=True,
    )

    for index in range(locator.count()):
        item = locator.nth(index)

        try:
            if item.is_visible():
                item.click()
                return
        except Exception:
            continue

    raise RuntimeError(
        f"没有找到可点击文本: {text}"
    )


def get_current_mode(
        page: Page,
) -> str | None:
    button = find_mode_button(page)

    if button is None:
        return None

    return button.get_attribute(
        "aria-label"
    )


def collect_controls(
        page: Page,
) -> list[dict]:
    return page.locator(
        """
        button,
        a,
        [role="button"],
        [role="menu"],
        [role="menuitem"],
        [role="option"],
        [role="textbox"]
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

            return {
                index,
                tag: el.tagName,
                visible,

                text:
                    (
                        el.innerText ||
                        el.textContent ||
                        ""
                    )
                    .trim()
                    .slice(0, 500),

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

                aria_expanded:
                    el.getAttribute(
                        "aria-expanded"
                    ),

                aria_pressed:
                    el.getAttribute(
                        "aria-pressed"
                    ),

                data_state:
                    el.getAttribute(
                        "data-state"
                    ),

                data_session_switch_target:
                    el.getAttribute(
                        "data-session-switch-target"
                    ),

                disabled:
                    el.disabled === true,

                href:
                    el.getAttribute("href"),

                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height
            };
        })
        """
    )


def collect_interesting_nodes(
        page: Page,
) -> list[dict]:
    """
    抓可能与消息、Markdown、回答区域有关的节点。

    当前阶段故意放宽范围，后面再根据真实结果
    收缩 selector。
    """

    return page.locator(
        """
        article,
        main,
        [data-testid],
        [data-message-id],
        [data-role],
        [class*="message"],
        [class*="answer"],
        [class*="markdown"],
        [class*="chat"]
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

            return {
                index,
                tag: el.tagName,
                visible,

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

                role:
                    el.getAttribute("role")
            };
        })
        """
    )


def capture(
        page: Page,
        output_dir: Path,
        name: str,
) -> None:
    print(f"[CAPTURE] {name}")

    page.screenshot(
        path=str(
            output_dir / f"{name}.png"
        ),
        full_page=True,
    )

    (
            output_dir / f"{name}.html"
    ).write_text(
        page.content(),
        encoding="utf-8",
    )

    save_json(
        output_dir /
        f"{name}_controls.json",
        collect_controls(page),
    )

    save_json(
        output_dir /
        f"{name}_interesting_nodes.json",
        collect_interesting_nodes(page),
    )

    (
            output_dir /
            f"{name}_body_text.txt"
    ).write_text(
        page.locator("body").inner_text(),
        encoding="utf-8",
    )


def wait_for_page_stability(
        page: Page,
        timeout_seconds: int = 30,
        stable_rounds: int = 3,
) -> dict:
    start = time.time()

    last_text = None
    stable_count = 0

    timeline = []

    while (
            time.time() - start
            < timeout_seconds
    ):
        current_text = (
            page.locator("body")
            .inner_text()
        )

        current_length = len(
            current_text
        )

        changed = (
                current_text != last_text
        )

        timeline.append(
            {
                "elapsed_seconds":
                    round(
                        time.time() - start,
                        2,
                    ),
                "text_length":
                    current_length,
                "changed":
                    changed,
            }
        )

        if changed:
            stable_count = 0
        else:
            stable_count += 1

        if stable_count >= stable_rounds:
            return {
                "stable": True,
                "timeline": timeline,
            }

        last_text = current_text

        page.wait_for_timeout(1000)

    return {
        "stable": False,
        "timeline": timeline,
    }


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
            OUTPUT_DIR /
            f"qwen_response_investigation_{timestamp}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as playwright:

        context = (
            playwright.chromium
            .launch_persistent_context(
                user_data_dir=str(
                    PROFILE_DIR
                ),
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

        # ==================================
        # 1. 初始状态
        # ==================================

        print(
            "[MODE] initial:",
            get_current_mode(page),
        )

        capture(
            page,
            output_dir,
            "01_initial",
        )

        # ==================================
        # 2. 切换到思考研究
        # ==================================

        mode_button = find_mode_button(
            page
        )

        if mode_button is None:
            raise RuntimeError(
                "没有找到模式按钮"
            )

        print(
            "[CLICK] open mode menu"
        )

        mode_button.click()

        page.wait_for_timeout(500)

        click_visible_text(
            page,
            "思考研究",
        )

        page.wait_for_timeout(1000)

        research_mode = (
            get_current_mode(page)
        )

        print(
            "[MODE] after research:",
            research_mode,
        )

        capture(
            page,
            output_dir,
            "02_research_selected",
        )

        # ==================================
        # 3. 再切回快速
        # ==================================

        mode_button = find_mode_button(
            page
        )

        if mode_button is None:
            raise RuntimeError(
                "思考研究状态下找不到模式按钮"
            )

        mode_button.click()

        page.wait_for_timeout(300)

        click_visible_text(
            page,
            "快速",
        )

        page.wait_for_timeout(1000)

        quick_mode = (
            get_current_mode(page)
        )

        print(
            "[MODE] after quick:",
            quick_mode,
        )

        capture(
            page,
            output_dir,
            "03_quick_restored",
        )

        # ==================================
        # 4. 输入真实探针
        # ==================================

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

        input_box.fill(
            PROBE_TEXT
        )

        page.wait_for_timeout(500)

        print(
            "[SEND] disabled:",
            send_button.is_disabled(),
        )

        capture(
            page,
            output_dir,
            "04_before_send",
        )

        # ==================================
        # 5. 正式发送
        # ==================================

        print(
            "[SEND] probe question"
        )

        send_button.click()

        # 第一波快速时序
        timeline_points = [
            (100, "05_after_100ms"),
            (400, "06_after_500ms"),
            (500, "07_after_1s"),
            (1000, "08_after_2s"),
            (3000, "09_after_5s"),
            (5000, "10_after_10s"),
        ]

        for delay, name in timeline_points:
            page.wait_for_timeout(delay)

            capture(
                page,
                output_dir,
                name,
            )

        # ==================================
        # 6. 等页面文本稳定
        # ==================================

        print(
            "[WAIT] response stability"
        )

        stability = (
            wait_for_page_stability(
                page,
                timeout_seconds=30,
                stable_rounds=3,
            )
        )

        save_json(
            output_dir /
            "11_stability.json",
            stability,
        )

        capture(
            page,
            output_dir,
            "12_final",
        )

        print()
        print(
            "[PASS] response investigation completed"
        )

        print(
            "[MODE]",
            get_current_mode(page),
        )

        print(
            "[OUTPUT]",
            output_dir,
        )

        input(
            "观察最终页面后按 Enter 关闭浏览器..."
        )

        context.close()


if __name__ == "__main__":
    main()
