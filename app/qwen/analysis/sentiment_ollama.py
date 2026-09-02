from __future__ import annotations

import asyncio
import json
import socket
from typing import Any
from urllib import error, request

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment_errors import (
    SentimentProviderError,
)
from app.qwen.analysis.sentiment_models import (
    SentimentLabel,
)


class OllamaSentimentClassifier:
    name = "ollama"

    def __init__(
        self,
        *,
        model: str = "qwen2.5:7b",
        base_url: str = (
            "http://127.0.0.1:11434"
        ),
        timeout_seconds: int = 120,
    ) -> None:
        self.model = model
        self.base_url = (
            base_url.rstrip("/")
        )
        self.timeout_seconds = (
            timeout_seconds
        )

    async def classify(
        self,
        *,
        answer_text: str,
        target: MentionTarget,
    ) -> SentimentLabel:
        response = await asyncio.to_thread(
            self._request_classification,
            answer_text,
            target,
        )

        try:
            return self._extract_label(
                response
            )

        except ValueError as exc:
            raise SentimentProviderError(
                "invalid_response",
                str(exc),
            ) from exc

    def _request_classification(
        self,
        answer_text: str,
        target: MentionTarget,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是品牌舆情情感分类器。"
                        "只判断回答内容对目标品牌/产品"
                        "呈现出的态度，不判断问题本身。"
                        "\n\n"
                        "只允许三个标签："
                        "\npositive：明显正面、认可、"
                        "推荐、强调优势或积极价值；"
                        "\nneutral：主要是客观事实说明、"
                        "定义、介绍、条件性描述，"
                        "没有明显褒贬；"
                        "\nnegative：明显负面、批评、"
                        "风险、违规、处罚、争议、"
                        "质量或信誉问题。"
                        "\n\n"
                        "如果回答同时包含正负信息，"
                        "根据对目标整体呈现的主要倾向判断；"
                        "若主要是平衡客观陈述，判 neutral。"
                        "\n\n"
                        "必须只返回 JSON："
                        '{"label":"positive"} '
                        "或 "
                        '{"label":"neutral"} '
                        "或 "
                        '{"label":"negative"}。'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"目标ID：{target.target_id}\n"
                        "目标别名："
                        f"{', '.join(target.aliases)}\n\n"
                        "回答内容：\n"
                        f"{answer_text}"
                    ),
                },
            ],
            "options": {
                "temperature": 0,
            },
        }

        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        req = request.Request(
            (
                self.base_url
                + "/api/chat"
            ),
            data=body,
            headers={
                "Content-Type": (
                    "application/json"
                ),
            },
            method="POST",
        )

        try:
            with request.urlopen(
                req,
                timeout=self.timeout_seconds,
            ) as response:
                raw = response.read()

        except error.HTTPError as exc:
            status_code = exc.code

            if status_code == 429:
                error_type = (
                    "rate_limit"
                )

            elif (
                500
                <= status_code
                <= 599
            ):
                error_type = (
                    "transient_api_error"
                )

            else:
                error_type = (
                    "api_error"
                )

            raise SentimentProviderError(
                error_type,
                (
                    "ollama HTTP error: "
                    f"{status_code}"
                ),
                status_code=status_code,
            ) from exc

        except (
            TimeoutError,
            socket.timeout,
        ) as exc:
            raise SentimentProviderError(
                "timeout",
                "ollama request timed out",
            ) from exc

        except error.URLError as exc:
            if isinstance(
                exc.reason,
                (
                    TimeoutError,
                    socket.timeout,
                ),
            ):
                raise SentimentProviderError(
                    "timeout",
                    "ollama request timed out",
                ) from exc

            raise SentimentProviderError(
                "network_error",
                (
                    "ollama network error: "
                    f"{exc.reason}"
                ),
            ) from exc

        except OSError as exc:
            raise SentimentProviderError(
                "network_error",
                (
                    "ollama network error: "
                    f"{exc}"
                ),
            ) from exc

        try:
            decoded = raw.decode(
                "utf-8"
            )

            parsed = json.loads(
                decoded
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise SentimentProviderError(
                "invalid_response",
                (
                    "ollama response is not "
                    "valid JSON"
                ),
            ) from exc

        if not isinstance(
            parsed,
            dict,
        ):
            raise SentimentProviderError(
                "invalid_response",
                (
                    "ollama response must "
                    "be a JSON object"
                ),
            )

        return parsed

    @staticmethod
    def _extract_label(
        response: dict[str, Any],
    ) -> SentimentLabel:
        message = response.get(
            "message"
        )

        if not isinstance(
            message,
            dict,
        ):
            raise ValueError(
                "ollama response missing message"
            )

        content = message.get(
            "content"
        )

        if not isinstance(
            content,
            str,
        ):
            raise ValueError(
                "ollama response missing content"
            )

        try:
            data = json.loads(
                content
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "ollama sentiment output "
                "is not valid JSON"
            ) from exc

        label = str(
            data.get(
                "label",
                "",
            )
        ).strip().lower()

        if label not in {
            "positive",
            "neutral",
            "negative",
        }:
            raise ValueError(
                "unsupported ollama "
                f"sentiment label: {label!r}"
            )

        return label  # type: ignore[return-value]
