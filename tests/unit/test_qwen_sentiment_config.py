from __future__ import annotations

import pytest

from app.qwen.analysis.sentiment_config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_RETRY_BACKOFF_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    load_sentiment_config,
)


def test_default_sentiment_config(
    monkeypatch,
):
    for name in (
        "SENTIMENT_PROVIDER",
        "SENTIMENT_MODEL",
        "SENTIMENT_BASE_URL",
        "SENTIMENT_REQUEST_TIMEOUT_SECONDS",
        "SENTIMENT_MAX_RETRIES",
        "SENTIMENT_RETRY_BACKOFF_SECONDS",
    ):
        monkeypatch.delenv(
            name,
            raising=False,
        )

    config = (
        load_sentiment_config()
    )

    assert (
        config.provider
        == DEFAULT_PROVIDER
    )

    assert (
        config.model
        == DEFAULT_MODEL
    )

    assert (
        config.base_url
        == DEFAULT_BASE_URL
    )

    assert (
        config.timeout_seconds
        == DEFAULT_TIMEOUT_SECONDS
    )

    assert (
        config.max_retries
        == DEFAULT_MAX_RETRIES
    )

    assert (
        config.retry_backoff_seconds
        == DEFAULT_RETRY_BACKOFF_SECONDS
    )


def test_load_sentiment_config_from_env(
    monkeypatch,
):
    monkeypatch.setenv(
        "SENTIMENT_PROVIDER",
        "OLLAMA",
    )

    monkeypatch.setenv(
        "SENTIMENT_MODEL",
        "test-model",
    )

    monkeypatch.setenv(
        "SENTIMENT_BASE_URL",
        "http://localhost:9999/",
    )

    monkeypatch.setenv(
        "SENTIMENT_REQUEST_TIMEOUT_SECONDS",
        "180",
    )

    monkeypatch.setenv(
        "SENTIMENT_MAX_RETRIES",
        "3",
    )

    monkeypatch.setenv(
        "SENTIMENT_RETRY_BACKOFF_SECONDS",
        "1,2.5,5",
    )

    config = (
        load_sentiment_config()
    )

    assert config.provider == "ollama"
    assert config.model == "test-model"

    assert (
        config.base_url
        == "http://localhost:9999"
    )

    assert (
        config.timeout_seconds
        == 180
    )

    assert config.max_retries == 3

    assert (
        config.retry_backoff_seconds
        == (
            1.0,
            2.5,
            5.0,
        )
    )


def test_invalid_provider_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "SENTIMENT_PROVIDER",
        "openai",
    )

    with pytest.raises(
        ValueError,
        match=(
            "unsupported sentiment provider"
        ),
    ):
        load_sentiment_config()


def test_invalid_timeout_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "SENTIMENT_REQUEST_TIMEOUT_SECONDS",
        "0",
    )

    with pytest.raises(
        ValueError,
        match=(
            "SENTIMENT_REQUEST_TIMEOUT_SECONDS"
        ),
    ):
        load_sentiment_config()


def test_invalid_retry_count_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "SENTIMENT_MAX_RETRIES",
        "-1",
    )

    with pytest.raises(
        ValueError,
        match="SENTIMENT_MAX_RETRIES",
    ):
        load_sentiment_config()


def test_invalid_backoff_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "SENTIMENT_RETRY_BACKOFF_SECONDS",
        "3,abc",
    )

    with pytest.raises(
        ValueError,
        match=(
            "SENTIMENT_RETRY_BACKOFF_SECONDS"
        ),
    ):
        load_sentiment_config()
