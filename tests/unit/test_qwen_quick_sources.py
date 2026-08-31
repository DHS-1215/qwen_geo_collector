from __future__ import annotations

import json
from unittest.mock import MagicMock

from app.qwen.runner import QwenRunner


def make_source_card(
    *,
    req_id: str,
    rank: int,
    title: str,
    url: str,
) -> MagicMock:
    card = MagicMock()

    card.get_attribute.return_value = json.dumps(
        {
            "req_id": req_id,
            "refer_num": str(rank),
            "title": title,
            "url": url,
            "ref_url": url,
        },
        ensure_ascii=False,
    )

    return card


def test_quick_sources_extracts_structured_sources(
    monkeypatch,
) -> None:
    runner = QwenRunner(
        page=MagicMock()
    )

    answer_wrap = MagicMock()

    req_id = "req-123"

    cards = [
        make_source_card(
            req_id=req_id,
            rank=2,
            title="新华网文章",
            url="https://example.com/2",
        ),
        make_source_card(
            req_id=req_id,
            rank=1,
            title="人民网文章",
            url="https://example.com/1",
        ),
    ]

    monkeypatch.setattr(
        runner,
        "_get_quick_source_req_id",
        lambda _answer_wrap: req_id,
    )

    monkeypatch.setattr(
        runner,
        "_open_quick_sources",
        lambda _answer_wrap, _req_id: cards,
    )

    sources = runner._extract_quick_sources(
        answer_wrap
    )

    assert len(sources) == 2

    assert sources[0].rank == 1
    assert sources[0].title == "人民网文章"
    assert (
        sources[0].url
        == "https://example.com/1"
    )

    assert sources[1].rank == 2
    assert sources[1].title == "新华网文章"
    assert (
        sources[1].url
        == "https://example.com/2"
    )


def test_quick_sources_reuses_open_panel(
    monkeypatch,
) -> None:
    runner = QwenRunner(
        page=MagicMock()
    )

    answer_wrap = MagicMock()

    existing_cards = [
        MagicMock(),
        MagicMock(),
    ]

    monkeypatch.setattr(
        runner,
        "_get_quick_source_cards",
        lambda _req_id: existing_cards,
    )

    cards = runner._open_quick_sources(
        answer_wrap,
        "req-123",
    )

    assert cards == existing_cards

    # 面板已经打开时，
    # 不应该再去寻找并点击“X篇来源”
    answer_wrap.get_by_text.assert_not_called()


def test_quick_sources_returns_empty_when_no_entry(
    monkeypatch,
) -> None:
    runner = QwenRunner(
        page=MagicMock()
    )

    answer_wrap = MagicMock()

    monkeypatch.setattr(
        runner,
        "_get_quick_source_req_id",
        lambda _answer_wrap: None,
    )

    sources = runner._extract_quick_sources(
        answer_wrap
    )

    assert sources == []
