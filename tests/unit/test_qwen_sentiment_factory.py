from __future__ import annotations

import pytest

from app.qwen.analysis.sentiment_config import (
    SentimentConfig,
)
from app.qwen.analysis.sentiment_factory import (
    create_sentiment_classifier,
)
from app.qwen.analysis.sentiment_ollama import (
    OllamaSentimentClassifier,
)
from app.qwen.analysis.sentiment_retry import (
    RetryingSentimentClassifier,
)


def test_create_ollama_classifier():
    config = SentimentConfig(
        provider="ollama",
        model="test-model",
        base_url=(
            "http://localhost:11434"
        ),
        timeout_seconds=180,
        max_retries=3,
        retry_backoff_seconds=(
            1.0,
            2.0,
        ),
    )

    classifier = (
        create_sentiment_classifier(
            config
        )
    )

    assert isinstance(
        classifier,
        RetryingSentimentClassifier,
    )

    assert isinstance(
        classifier.classifier,
        OllamaSentimentClassifier,
    )

    assert (
        classifier.max_retries
        == 3
    )

    assert (
        classifier.retry_backoff_seconds
        == (
            1.0,
            2.0,
        )
    )


def test_factory_preserves_provider_name():
    classifier = (
        create_sentiment_classifier(
            SentimentConfig()
        )
    )

    assert (
        classifier.name
        == "ollama"
    )


def test_factory_rejects_unknown_provider():
    config = SentimentConfig(
        provider="unknown",
    )

    with pytest.raises(
        ValueError,
        match=(
            "unsupported sentiment provider"
        ),
    ):
        create_sentiment_classifier(
            config
        )
