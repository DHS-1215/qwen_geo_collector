from __future__ import annotations

import json
import re
import time

from app.qwen.browser import QwenBrowserSession
from app.qwen.selectors import ANSWER_WRAP_SELECTOR


SOURCE_CARD_SELECTOR = (
    '[data-c="refer_panel"]'
    '[data-d="card"]'
)


def wait_for_cards(
    page,
    timeout_seconds: int = 5,
) -> int:
    start = time.monotonic()

    while (
        time.monotonic() - start
        < timeout_seconds
    ):
        count = page.locator(
            SOURCE_CARD_SELECTOR
        ).count()

        if count > 0:
            return count

        page.wait_for_timeout(200)

    return 0


def main() -> None:
    session = QwenBrowserSession()

    try:
        page = session.connect()

        print("[PAGE]", page.url)

        answers = page.locator(
            ANSWER_WRAP_SELECTOR
        )

        if answers.count() == 0:
            print("[STOP] no answer")
            return

        answer_wrap = answers.last

        source_entry = (
            answer_wrap.get_by_text(
                re.compile(
                    r"^\s*\d+\s*[篇条]来源\s*$"
                )
            )
        )

        print(
            "[QUICK SOURCE ENTRY]",
            source_entry.count(),
        )

        if source_entry.count() == 0:
            print(
                "[QUICK SOURCE] "
                "no source entry"
            )
            return

        print(
            "[QUICK SOURCE TEXT]",
            repr(
                source_entry.first
                .inner_text()
                .strip()
            ),
        )

        # =========================================
        # 先检查来源面板是不是已经打开
        # =========================================
        cards = page.locator(
            SOURCE_CARD_SELECTOR
        )

        before_count = cards.count()

        print(
            "[SOURCE CARDS BEFORE CLICK]",
            before_count,
        )

        if before_count == 0:
            print(
                "[QUICK SOURCE] "
                "panel closed, opening"
            )

            try:
                source_entry.first.click(
                    timeout=3000
                )

                print(
                    "[QUICK SOURCE] "
                    "click success"
                )

            except Exception as exc:
                print(
                    "[QUICK SOURCE] "
                    "normal click failed:",
                    type(exc).__name__,
                )

                source_entry.first.evaluate(
                    "el => el.click()"
                )

                print(
                    "[QUICK SOURCE] "
                    "DOM click success"
                )

            card_count = wait_for_cards(
                page
            )

        else:
            print(
                "[QUICK SOURCE] "
                "panel already open"
            )

            card_count = before_count

        print(
            "[SOURCE CARDS]",
            card_count,
        )

        if card_count == 0:
            print(
                "[STOP] "
                "source panel opened "
                "but no cards found"
            )
            return

        # =========================================
        # 提取
        # =========================================
        cards = page.locator(
            SOURCE_CARD_SELECTOR
        )

        sources = []
        seen_urls: set[str] = set()

        for index in range(
            cards.count()
        ):
            card = cards.nth(index)

            raw = card.get_attribute(
                "data-click-extra"
            )

            if not raw:
                continue

            try:
                data = json.loads(raw)

            except json.JSONDecodeError:
                print(
                    f"[SOURCE {index + 1}] "
                    "invalid JSON"
                )
                continue

            title = (
                data.get("title")
                or ""
            ).strip()

            url = (
                data.get("ref_url")
                or data.get("url")
                or ""
            ).strip()

            rank_raw = (
                data.get("refer_num")
                or str(index + 1)
            )

            try:
                rank = int(rank_raw)
            except ValueError:
                rank = index + 1

            if not title or not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            sources.append(
                {
                    "rank": rank,
                    "title": title,
                    "url": url,
                }
            )

            print()
            print(
                f"[SOURCE {rank}]",
                title,
            )
            print(
                "          ",
                url,
            )

        print()
        print(
            "[QUICK SOURCES EXTRACTED]",
            len(sources),
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()
