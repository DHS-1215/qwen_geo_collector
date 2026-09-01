from __future__ import annotations

import asyncio

import pytest

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment_ollama import (
    OllamaSentimentClassifier,
)


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao",
        aliases=[
            "鸿茅药酒",
        ],
    )


def test_extract_positive():
    result = (
        OllamaSentimentClassifier
        ._extract_label(
            {
                "message": {
                    "content": (
                        '{"label":"positive"}'
                    )
                }
            }
        )
    )

    assert result == "positive"


def test_extract_neutral():
    result = (
        OllamaSentimentClassifier
        ._extract_label(
            {
                "message": {
                    "content": (
                        '{"label":"neutral"}'
                    )
                }
            }
        )
    )

    assert result == "neutral"


def test_extract_negative():
    result = (
        OllamaSentimentClassifier
        ._extract_label(
            {
                "message": {
                    "content": (
                        '{"label":"negative"}'
                    )
                }
            }
        )
    )

    assert result == "negative"


def test_invalid_json_is_rejected():
    with pytest.raises(
        ValueError
    ):
        (
            OllamaSentimentClassifier
            ._extract_label(
                {
                    "message": {
                        "content": "negative"
                    }
                }
            )
        )


def test_invalid_label_is_rejected():
    with pytest.raises(
        ValueError
    ):
        (
            OllamaSentimentClassifier
            ._extract_label(
                {
                    "message": {
                        "content": (
                            '{"label":"mixed"}'
                        )
                    }
                }
            )
        )


def test_classify_uses_provider_response(
    monkeypatch,
):
    classifier = (
        OllamaSentimentClassifier()
    )

    def fake_request(
        answer_text,
        target,
    ):
        assert (
            "鸿茅药酒"
            in answer_text
        )

        assert (
            target.target_id
            == "hongmao"
        )

        return {
            "message": {
                "content": (
                    '{"label":"neutral"}'
                )
            }
        }

    monkeypatch.setattr(
        classifier,
        "_request_classification",
        fake_request,
    )

    result = asyncio.run(
        classifier.classify(
            answer_text=(
                "鸿茅药酒属于药品。"
            ),
            target=_target(),
        )
    )

    assert result == "neutral"
