from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from app.qwen.exceptions import (
    QwenConnectionError,
)
from app.qwen.selectors import (
    QWEN_DOMAIN,
)


class QwenBrowserSession:
    def __init__(
            self,
            cdp_url: str = "http://127.0.0.1:9222",
    ) -> None:
        self.cdp_url = cdp_url

        self._playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def connect(self) -> Page:
        self._playwright = (
            sync_playwright().start()
        )

        try:
            self.browser = (
                self._playwright.chromium
                .connect_over_cdp(
                    self.cdp_url
                )
            )
        except Exception as exc:
            self._playwright.stop()
            self._playwright = None

            raise QwenConnectionError(
                f"无法连接 Chrome CDP: "
                f"{self.cdp_url}"
            ) from exc

        if not self.browser.contexts:
            raise QwenConnectionError(
                "Chrome 中不存在 browser context"
            )

        self.context = (
            self.browser.contexts[0]
        )

        self.page = self._find_qwen_page()

        return self.page

    def _find_qwen_page(self) -> Page:
        if self.context is None:
            raise QwenConnectionError(
                "browser context 尚未初始化"
            )

        candidate_pages: list[Page] = []

        for page in self.context.pages:
            hostname = (
                    urlparse(page.url).hostname
                    or ""
            ).lower()

            if hostname in {
                "www.qianwen.com",
                "qianwen.com",
            }:
                candidate_pages.append(
                    page
                )

        if not candidate_pages:
            opened_pages = [
                page.url
                for page in self.context.pages
            ]

            raise QwenConnectionError(
                "Chrome 中没有打开千问主聊天页面。"
                f"当前页面: {opened_pages}"
            )

        page = candidate_pages[0]

        print(
            "[QWEN PAGE]",
            page.url,
        )

        return page

    def close(self) -> None:
        """
        只结束 Playwright 客户端。

        不主动 browser.close()，
        避免把用户手工启动的 Chrome 一起关闭。
        """

        self.page = None
        self.context = None
        self.browser = None

        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
