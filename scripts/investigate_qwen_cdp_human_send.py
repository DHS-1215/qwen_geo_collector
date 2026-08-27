from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Locator, Page, sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT_DIR / "output"

CDP_URL = "http://127.0.0.1:9222"

INPUT_SELECTOR = (
    '[role="textbox"]'
    '[data-slate-editor="true"]'
    '[contenteditable="true"]'
)

SEND_BUTTON_SELECTOR = (
    'button[aria-label="发送消息"]'
)

PROBE_TEXT = "请只回答：QWEN_GEO_CDP_PROBE_OK"


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


def get_qwen_page(context) -> Page:
    for page in context.pages:
        if "qianwen.com" in page.url:
            return page

    raise RuntimeError("没有找到千问页面")


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


def collect_controls(page: Page) -> list[dict]:
    return page.locator(
        """
        button,
        a,
        [role="button"],
        [role="textbox"],
        [data-testid],
        [data-message-id]
        """
    ).evaluate_all(
        """
        elements => elements.map((el, index) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);

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
                    .slice(0, 1000),

                role:
                    el.getAttribute("role"),

                aria_label:
                    el.getAttribute("aria-label"),

                aria_disabled:
                    el.getAttribute("aria-disabled"),

                disabled:
                    el.disabled === true,

                data_testid:
                    el.getAttribute("data-testid"),

                data_message_id:
                    el.getAttribute("data-message-id"),

                class_name:
                    typeof el.className === "string"
                        ? el.className
                        : null
            };
        })
        """
    )


def collect_candidate_nodes(page: Page) -> list[dict]:
    return page.locator(
        """
        article,
        main,
        [data-testid],
        [data-message-id],
        [class*="message"],
        [class*="answer"],
        [class*="markdown"],
        [class*="chat"]
        """
    ).evaluate_all(
        """
        elements => elements.map((el, index) => {
            const rect = el.getBoundingClientRect();

            return {
                index,
                tag: el.tagName,

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

                role:
                    el.getAttribute("role"),

                data_testid:
                    el.getAttribute("data-testid"),

                data_message_id:
                    el.getAttribute("data-message-id"),

                class_name:
                    typeof el.className === "string"
                        ? el.className
                        : null,

                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height
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

    (
        output_dir / f"{name}_body.txt"
    ).write_text(
        page.locator("body").inner_text(),
        encoding="utf-8",
    )

    save_json(
        output_dir / f"{name}_controls.json",
        collect_controls(page),
    )

    save_json(
        output_dir / f"{name}_nodes.json",
        collect_candidate_nodes(page),
    )


def wait_for_question_to_leave_input(
    input_box: Locator,
    timeout_seconds: int = 60,
) -> bool:
    start = time.time()

    while time.time() - start < timeout_seconds:

        try:
            text = input_box.inner_text().strip()
        except Exception:
            text = ""

        if not text:
            return True

        time.sleep(0.2)

    return False


def monitor_response(
    page: Page,
    output_dir: Path,
    seconds: int = 20,
) -> None:
    start = time.time()

    last_body = None

    timeline = []

    checkpoints = {
        0: "03_after_send",
        1: "04_after_1s",
        2: "05_after_2s",
        5: "06_after_5s",
        10: "07_after_10s",
        20: "08_after_20s",
    }

    captured = set()

    while True:
        elapsed = int(
            time.time() - start
        )

        body = (
            page.locator("body")
            .inner_text()
        )

        timeline.append(
            {
                "elapsed_seconds": elapsed,
                "body_length": len(body),
                "changed": body != last_body,
                "risk_control":
                    detect_risk_control(page),
            }
        )

        last_body = body

        for second, name in checkpoints.items():

            if (
                elapsed >= second
                and second not in captured
            ):
                capture(
                    page,
                    output_dir,
                    name,
                )

                captured.add(second)

        if detect_risk_control(page):
            print(
                "[RISK] verification detected"
            )
            break

        if elapsed >= seconds:
            break

        page.wait_for_timeout(500)

    save_json(
        output_dir / "response_timeline.json",
        timeline,
    )


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
        OUTPUT_DIR /
        f"qwen_cdp_human_send_{timestamp}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as playwright:

        print(f"[CONNECT] {CDP_URL}")

        browser = (
            playwright.chromium
            .connect_over_cdp(
                CDP_URL
            )
        )

        if not browser.contexts:
            raise RuntimeError(
                "没有找到 browser context"
            )

        context = browser.contexts[0]

        page = get_qwen_page(
            context
        )

        print(
            "[PASS] Qwen page connected"
        )

        print(
            "[RISK] initial:",
            detect_risk_control(page),
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

        # --------------------------
        # 自动填写
        # --------------------------

        input_box.fill(
            PROBE_TEXT
        )

        page.wait_for_timeout(500)

        print(
            "[FILL]",
            input_box.inner_text(),
        )

        print(
            "[SEND] disabled:",
            send_button.is_disabled(),
        )

        print(
            "[RISK] after fill:",
            detect_risk_control(page),
        )

        capture(
            page,
            output_dir,
            "01_before_human_send",
        )

        # --------------------------
        # 人工点击
        # --------------------------

        print()
        print("=" * 70)
        print(
            "现在请你在 Chrome 中"
            "亲手点击“发送消息”按钮。"
        )
        print(
            "不要在 PowerShell 按 Enter。"
        )
        print(
            "程序会自动判断输入框"
            "什么时候被清空。"
        )
        print("=" * 70)

        sent = (
            wait_for_question_to_leave_input(
                input_box,
                timeout_seconds=60,
            )
        )

        if not sent:
            raise RuntimeError(
                "60 秒内没有检测到问题发送"
            )

        print(
            "[PASS] human send detected"
        )

        page.wait_for_timeout(100)

        capture(
            page,
            output_dir,
            "02_send_detected",
        )

        # --------------------------
        # 自动观察回答
        # --------------------------

        print(
            "[MONITOR] response"
        )

        monitor_response(
            page,
            output_dir,
            seconds=20,
        )

        print(
            "[RISK] final:",
            detect_risk_control(page),
        )

        capture(
            page,
            output_dir,
            "09_final",
        )

        print()
        print(
            "[PASS] investigation completed"
        )

        print(
            "[OUTPUT]",
            output_dir,
        )

        input(
            "观察页面后按 Enter 结束连接..."
        )

        # 这里故意不调用 browser.close()
        # Chrome 是用户自己启动的，让它继续保持打开。


if __name__ == "__main__":
    main()