from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BACKOFF_SECONDS = (
    3.0,
    8.0,
)


@dataclass(frozen=True)
class SentimentConfig:
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL

    timeout_seconds: int = (
        DEFAULT_TIMEOUT_SECONDS
    )

    max_retries: int = (
        DEFAULT_MAX_RETRIES
    )

    retry_backoff_seconds: tuple[
        float,
        ...
    ] = DEFAULT_RETRY_BACKOFF_SECONDS


def _parse_int(
    value: str | None,
    *,
    default: int,
    name: str,
    minimum: int = 0,
) -> int:
    if value is None:
        return default

    try:
        parsed = int(
            value.strip()
        )
    except ValueError as exc:
        raise ValueError(
            f"{name} must be an integer"
        ) from exc

    if parsed < minimum:
        raise ValueError(
            f"{name} must be >= {minimum}"
        )

    return parsed


def _parse_backoff(
    value: str | None,
) -> tuple[float, ...]:
    if value is None:
        return (
            DEFAULT_RETRY_BACKOFF_SECONDS
        )

    raw_items = [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]

    if not raw_items:
        return ()

    try:
        parsed = tuple(
            float(item)
            for item in raw_items
        )
    except ValueError as exc:
        raise ValueError(
            "SENTIMENT_RETRY_BACKOFF_SECONDS "
            "must be comma-separated numbers"
        ) from exc

    if any(
        item < 0
        for item in parsed
    ):
        raise ValueError(
            "SENTIMENT_RETRY_BACKOFF_SECONDS "
            "must contain non-negative numbers"
        )

    return parsed


def load_sentiment_config() -> SentimentConfig:
    provider = os.getenv(
        "SENTIMENT_PROVIDER",
        DEFAULT_PROVIDER,
    ).strip().lower()

    if provider != "ollama":
        raise ValueError(
            "unsupported sentiment provider: "
            f"{provider}"
        )

    model = os.getenv(
        "SENTIMENT_MODEL",
        DEFAULT_MODEL,
    ).strip()

    if not model:
        raise ValueError(
            "SENTIMENT_MODEL cannot be empty"
        )

    base_url = os.getenv(
        "SENTIMENT_BASE_URL",
        DEFAULT_BASE_URL,
    ).strip().rstrip("/")

    if not base_url:
        raise ValueError(
            "SENTIMENT_BASE_URL cannot be empty"
        )

    timeout_seconds = _parse_int(
        os.getenv(
            "SENTIMENT_REQUEST_TIMEOUT_SECONDS"
        ),
        default=DEFAULT_TIMEOUT_SECONDS,
        name=(
            "SENTIMENT_REQUEST_TIMEOUT_SECONDS"
        ),
        minimum=1,
    )

    max_retries = _parse_int(
        os.getenv(
            "SENTIMENT_MAX_RETRIES"
        ),
        default=DEFAULT_MAX_RETRIES,
        name="SENTIMENT_MAX_RETRIES",
        minimum=0,
    )

    retry_backoff_seconds = (
        _parse_backoff(
            os.getenv(
                "SENTIMENT_RETRY_BACKOFF_SECONDS"
            )
        )
    )

    return SentimentConfig(
        provider=provider,
        model=model,
        base_url=base_url,
        timeout_seconds=(
            timeout_seconds
        ),
        max_retries=max_retries,
        retry_backoff_seconds=(
            retry_backoff_seconds
        ),
    )
