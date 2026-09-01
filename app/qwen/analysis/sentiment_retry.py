from __future__ import annotations

import asyncio

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment import (
    SentimentClassifier,
)
from app.qwen.analysis.sentiment_errors import (
    SentimentProviderError,
)
from app.qwen.analysis.sentiment_models import (
    SentimentLabel,
)


class RetryingSentimentClassifier:
    def __init__(
        self,
        classifier: SentimentClassifier,
        *,
        max_retries: int = 2,
        retry_backoff_seconds: tuple[
            float,
            ...
        ] = (
            3.0,
            8.0,
        ),
    ) -> None:
        if max_retries < 0:
            raise ValueError(
                "max_retries must be >= 0"
            )

        if any(
            delay < 0
            for delay
            in retry_backoff_seconds
        ):
            raise ValueError(
                "retry backoff must "
                "be non-negative"
            )

        self.classifier = (
            classifier
        )

        self.max_retries = (
            max_retries
        )

        self.retry_backoff_seconds = (
            retry_backoff_seconds
        )

    @property
    def name(
        self,
    ) -> str:
        return str(
            getattr(
                self.classifier,
                "name",
                type(
                    self.classifier
                ).__name__,
            )
        )

    def _get_delay(
        self,
        retry_index: int,
    ) -> float:
        if not (
            self.retry_backoff_seconds
        ):
            return 0.0

        index = min(
            retry_index,
            len(
                self.retry_backoff_seconds
            )
            - 1,
        )

        return (
            self.retry_backoff_seconds[
                index
            ]
        )

    async def classify(
        self,
        *,
        answer_text: str,
        target: MentionTarget,
    ) -> SentimentLabel:
        for attempt in range(
            self.max_retries + 1
        ):
            try:
                return await (
                    self.classifier.classify(
                        answer_text=(
                            answer_text
                        ),
                        target=target,
                    )
                )

            except (
                SentimentProviderError
            ) as exc:
                if (
                    not exc.retryable
                    or attempt
                    >= self.max_retries
                ):
                    raise

                delay = (
                    self._get_delay(
                        attempt
                    )
                )

                if delay > 0:
                    await asyncio.sleep(
                        delay
                    )

        raise RuntimeError(
            "unreachable retry state"
        )
