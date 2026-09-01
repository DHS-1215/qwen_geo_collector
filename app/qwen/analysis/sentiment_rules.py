from __future__ import annotations

from dataclasses import dataclass
import re

from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.mention import (
    normalize_text,
)


@dataclass(frozen=True)
class SentimentRuleDecision:
    rule_hit: bool
    final_sentiment: str | None = None
    reason: str | None = None
    evidence: tuple[str, ...] = ()


NEGATIVE_RULES: tuple[
    tuple[str, tuple[str, ...]],
    ...,
] = (
    (
        "historical_case",
        (
            "谭秦东",
            "跨省抓捕",
            "跨省被抓",
        ),
    ),
    (
        "false_advertising",
        (
            "虚假宣传",
            "夸大宣传",
        ),
    ),
    (
        "advertising_violation",
        (
            "违法广告",
            "违规广告",
            "广告违规",
            "广告屡遭查处",
        ),
    ),
    (
        "regulatory_action",
        (
            "行政处罚",
            "监管处罚",
            "被处罚",
            "责令整改",
            "暂停销售",
            "暂停广告",
            "停止销售",
            "停售",
        ),
    ),
)


NEGATION_MARKERS = (
    "没有",
    "并未",
    "未被",
    "并非",
    "不是",
    "不存在",
    "未发现",
    "不能证明",
    "不能说明",
    "不能据此认定",
    "不等于",
    "并不意味着",
)


def apply_negative_priority_rules(
    *,
    answer_text: str,
    target: MentionTarget,
) -> SentimentRuleDecision:
    if target.target_id != "hongmao":
        return SentimentRuleDecision(
            rule_hit=False
        )

    text = normalize_text(
        answer_text
    )

    if not text:
        return SentimentRuleDecision(
            rule_hit=False
        )

    evidence: list[str] = []
    reasons: list[str] = []

    for rule_name, terms in NEGATIVE_RULES:
        for term in terms:
            normalized_term = (
                normalize_text(term)
            )

            for match in re.finditer(
                re.escape(
                    normalized_term
                ),
                text,
            ):
                if _is_negated(
                    text,
                    match.start(),
                ):
                    continue

                evidence.append(
                    _extract_evidence(
                        text,
                        match.start(),
                        match.end(),
                    )
                )

                reasons.append(
                    rule_name
                )

    if not evidence:
        return SentimentRuleDecision(
            rule_hit=False
        )

    unique_evidence = tuple(
        dict.fromkeys(
            evidence
        )
    )

    unique_reasons = list(
        dict.fromkeys(
            reasons
        )
    )

    return SentimentRuleDecision(
        rule_hit=True,
        final_sentiment="negative",
        reason=(
            "negative priority rule: "
            + ", ".join(
                unique_reasons
            )
        ),
        evidence=unique_evidence,
    )


def _is_negated(
    text: str,
    match_start: int,
) -> bool:
    prefix_start = max(
        0,
        match_start - 14,
    )

    prefix = text[
        prefix_start:match_start
    ]

    return any(
        marker in prefix
        for marker in NEGATION_MARKERS
    )


def _extract_evidence(
    text: str,
    start: int,
    end: int,
) -> str:
    evidence_start = max(
        0,
        start - 18,
    )

    evidence_end = min(
        len(text),
        end + 18,
    )

    return text[
        evidence_start:evidence_end
    ].strip()
