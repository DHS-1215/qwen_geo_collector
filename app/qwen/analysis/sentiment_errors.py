from __future__ import annotations

from typing import Literal


SentimentProviderErrorType = Literal[
    "rate_limit",
    "transient_api_error",
    "timeout",
    "network_error",
    "invalid_response",
    "validation_error",
    "api_error",
]


RETRYABLE_ERROR_TYPES = frozenset(
    {
        "rate_limit",
        "transient_api_error",
        "timeout",
        "network_error",
    }
)


class SentimentProviderError(
    RuntimeError
):
    def __init__(
        self,
        error_type: SentimentProviderErrorType,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(
            message
        )

        self.error_type = (
            error_type
        )

        self.status_code = (
            status_code
        )

    @property
    def retryable(
        self,
    ) -> bool:
        return (
            self.error_type
            in RETRYABLE_ERROR_TYPES
        )
