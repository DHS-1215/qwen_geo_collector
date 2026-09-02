from __future__ import annotations

from app.qwen.analysis.sentiment import (
    SentimentClassifier,
)
from app.qwen.analysis.sentiment_config import (
    SentimentConfig,
)
from app.qwen.analysis.sentiment_ollama import (
    OllamaSentimentClassifier,
)
from app.qwen.analysis.sentiment_retry import (
    RetryingSentimentClassifier,
)


def create_sentiment_classifier(
    config: SentimentConfig,
) -> SentimentClassifier:
    if config.provider != "ollama":
        raise ValueError(
            "unsupported sentiment provider: "
            f"{config.provider}"
        )

    base_classifier = (
        OllamaSentimentClassifier(
            model=config.model,
            base_url=config.base_url,
            timeout_seconds=(
                config.timeout_seconds
            ),
        )
    )

    return RetryingSentimentClassifier(
        base_classifier,
        max_retries=(
            config.max_retries
        ),
        retry_backoff_seconds=(
            config.retry_backoff_seconds
        ),
    )
