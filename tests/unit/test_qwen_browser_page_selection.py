from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.qwen.browser import (
    QwenBrowserSession,
)
from app.qwen.exceptions import (
    QwenConnectionError,
)


def make_page(
        url: str,
):
    page = Mock()
    page.url = url
    return page


def test_find_qwen_page_selects_main_chat_page() -> None:
    session = QwenBrowserSession()

    create_page = make_page(
        "https://create.qianwen.com/"
        "r/ai-studio-pc/main/gen"
    )

    chat_page = make_page(
        "https://www.qianwen.com/chat"
    )

    session.context = Mock()

    session.context.pages = [
        create_page,
        chat_page,
    ]

    result = session._find_qwen_page()

    assert result is chat_page


def test_find_qwen_page_rejects_create_subdomain() -> None:
    session = QwenBrowserSession()

    create_page = make_page(
        "https://create.qianwen.com/"
        "r/ai-studio-pc/main/gen"
    )

    session.context = Mock()

    session.context.pages = [
        create_page,
    ]

    with pytest.raises(
            QwenConnectionError,
            match="没有打开千问主聊天页面",
    ):
        session._find_qwen_page()


def test_find_qwen_page_accepts_root_domain() -> None:
    session = QwenBrowserSession()

    page = make_page(
        "https://qianwen.com/chat"
    )

    session.context = Mock()

    session.context.pages = [
        page,
    ]

    result = session._find_qwen_page()

    assert result is page
