from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT_DIR / "output"
PROFILE_DIR = ROOT_DIR / ".qwen_profile"

QWEN_URL = "https://www.qianwen.com/?ch=tongyi_redirect"

VIEWPORT = {
    "width": 1440,
    "height": 1000,
}


def save_json(path: Path, data) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def collect_candidates(page: Page) -> list[dict]:
    selector = """
    button,
    textarea,
    input,
    a,
    [role="button"],
    [contenteditable="true"]
    """

    return page.locator(selector).evaluate_all(
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
                index: index,
                tag: el.tagName,
                id: el.id || null,
                class_name:
                    typeof el.className === "string"
                        ? el.className
                        : null,
                role: el.getAttribute("role"),
                type: el.getAttribute("type"),
                aria_label: el.getAttribute("aria-label"),
                placeholder: el.getAttribute("placeholder"),
                title: el.getAttribute("title"),
                text:
                    (el.innerText || el.textContent || "")
                    .trim(),
                visible: visible,
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
        path=str(output_dir / f"{name}.png"),
        full_page=True,
    )

    (output_dir / f"{name}.html").write_text(
        page.content(),
        encoding="utf-8",
    )

    save_json(
        output_dir / f"{name}_candidates.json",
        collect_candidates(page),
    )

    save_json(
        output_dir / f"{name}_page_info.json",
        {
            "url": page.url,
            "title": page.title(),
            "ready_state": page.evaluate(
                "document.readyState"
            ),
            "viewport": page.viewport_size,
        },
    )


def main() -> None:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_dir = (
            OUTPUT_DIR
            / f"qwen_ui_investigation_{timestamp}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("Qwen GEO UI Investigation")
    print("=" * 70)
    print(f"Output : {output_dir}")
    print(f"Profile: {PROFILE_DIR}")
    print()

    with sync_playwright() as playwright:
        context = (
            playwright.chromium
            .launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                channel="chrome",
                headless=False,
                viewport=VIEWPORT,
            )
        )

        if context.pages:
            page = context.pages[0]
        else:
            page = context.new_page()

        print(f"[OPEN] {QWEN_URL}")

        page.goto(
            QWEN_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        page.wait_for_timeout(8000)

        capture(
            page,
            output_dir,
            "01_initial",
        )

        print()
        print("=" * 70)
        print("请观察浏览器页面。")
        print()
        print("如果需要登录，请手动完成登录。")
        print("如果已经登录，不需要进行其他操作。")
        print()
        print("完成后回到 PowerShell 按 Enter。")
        print("=" * 70)

        input()

        page.wait_for_timeout(3000)

        capture(
            page,
            output_dir,
            "02_after_login",
        )

        print()
        print("[PASS] Investigation completed.")
        print(f"[OUTPUT] {output_dir}")

        context.close()


if __name__ == "__main__":
    main()
