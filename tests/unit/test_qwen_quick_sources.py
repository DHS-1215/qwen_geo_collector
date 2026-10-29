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


def test_source_panel_records_cards_with_empty_urls(monkeypatch) -> None:
    from app.qwen.models import QwenAnswerResult
    from app.qwen.package.mapping import answer_result_to_geo_answer

    runner = QwenRunner(page=MagicMock())
    answer_wrap = MagicMock()
    req_id = "req-invalid"
    cards = [
        make_source_card(
            req_id=req_id,
            rank=i,
            title=f"Card {i}",
            url="",
        )
        for i in range(1, 11)
    ]
    monkeypatch.setattr(runner, "_get_quick_source_req_id", lambda _: req_id)
    monkeypatch.setattr(runner, "_open_quick_sources", lambda *_: cards)

    sources = runner._extract_quick_sources(answer_wrap)
    quality = runner._build_source_quality(
        sources, panel=runner._last_source_panel_diagnostics,
    )
    assert sources == []
    assert quality.status == "links_unavailable"
    assert quality.source_card_count == 10
    assert quality.invalid_url_count == 10
    assert quality.valid_source_count == 0

    result = QwenAnswerResult(
        question_id="Q002", question="Test", answer="Answer",
        turn_id="t", chat_url="https://qianwen.com/chat/t",
        mode="research", source_quality=quality,
    )
    mapped = answer_result_to_geo_answer(result, batch_id="batch-1")
    assert mapped.validation_status == "PASS_WITH_WARNINGS"
    assert mapped.source_collection_status == "failed"
    assert mapped.platform_meta_json["source_quality"]["invalid_url_count"] == 10


def test_research_falls_back_to_source_panel(monkeypatch) -> None:
    from app.qwen.models import QwenSource

    runner = QwenRunner(page=MagicMock())
    answer_wrap = MagicMock()
    monkeypatch.setattr(runner, "_expand_research_sources", lambda _: None)
    monkeypatch.setattr(runner, "_extract_sources", lambda _: [])

    def panel_extraction(_):
        runner._last_source_panel_diagnostics = {
            "entry_detected": True, "source_card_count": 1,
            "invalid_url_count": 0, "unreadable_card_count": 0,
        }
        return [QwenSource(rank=1, title="Article", url="https://example.com/1")]

    monkeypatch.setattr(runner, "_extract_quick_sources", panel_extraction)
    answer_wrap.locator.return_value.locator.return_value.count.return_value = 0
    sources, quality = runner._collect_research_sources(answer_wrap)
    assert len(sources) == 1
    assert quality.status == "success"
    assert quality.source_card_count == 1


def test_research_prefers_existing_workflow_sources(monkeypatch) -> None:
    from app.qwen.models import QwenSource

    runner = QwenRunner(page=MagicMock())
    answer_wrap = MagicMock()
    expected = [QwenSource(rank=1, title="Workflow", url="https://example.com/w")]
    monkeypatch.setattr(runner, "_expand_research_sources", lambda _: None)
    monkeypatch.setattr(runner, "_extract_sources", lambda _: expected)
    panel = MagicMock(side_effect=AssertionError("Panel should not open"))
    monkeypatch.setattr(runner, "_extract_quick_sources", panel)
    answer_wrap.locator.return_value.locator.return_value.count.return_value = 1
    sources, quality = runner._collect_research_sources(answer_wrap)
    assert sources == expected
    assert quality.status == "success"
    panel.assert_not_called()


def test_existing_answer_without_quality_remains_compatible() -> None:
    from app.qwen.models import QwenAnswerResult
    from app.qwen.package.mapping import answer_result_to_geo_answer

    result = QwenAnswerResult(
        question_id="Q001", question="Test", answer="Answer",
        turn_id="t", chat_url="https://qianwen.com/chat/t",
    )
    mapped = answer_result_to_geo_answer(result, batch_id="batch-1")
    assert result.source_quality.status == "unknown"
    assert mapped.validation_status == "PASS_WITH_WARNINGS"
    assert mapped.source_collection_status == "partial_success"


def test_historical_answer_with_sources_keeps_pass() -> None:
    from app.qwen.models import QwenAnswerResult, QwenSource
    from app.qwen.package.mapping import answer_result_to_geo_answer

    result = QwenAnswerResult(
        question_id="Q001",
        question="Test",
        answer="Answer",
        turn_id="t",
        chat_url="https://qianwen.com/chat/t",
        sources=[
            QwenSource(
                rank=1,
                title="Existing source",
                url="https://example.com/article",
            )
        ],
    )

    mapped = answer_result_to_geo_answer(
        result, batch_id="batch-1"
    )

    assert result.source_quality.status == "unknown"
    assert mapped.validation_status == "PASS"
    assert mapped.source_collection_status == "success"
