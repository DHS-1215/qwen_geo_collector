from __future__ import annotations

from typing import Protocol

from app.qwen.analysis.mention import (
    MentionResult,
)
from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment_models import (
    SentimentLabel,
    SentimentResult,
)
from app.qwen.analysis.sentiment_rules import (
    apply_negative_priority_rules,
)


class SentimentClassifier(Protocol):
    async def classify(
            self,
            *,
            answer_text: str,
            target: MentionTarget,
    ) -> SentimentLabel | str:
        ...


def should_classify_sentiment(
        *,
        is_valid_answer: bool,
        answer_text: str,
        mention: MentionResult,
) -> bool:
    if not is_valid_answer:
        return False

    if not answer_text.strip():
        return False

    return (
            mention.mention_count > 0
            and mention.mentioned
    )


async def analyze_sentiment(
        *,
        question_id: str,
        mode: str,
        answer_text: str,
        is_valid_answer: bool,
        mention: MentionResult,
        target: MentionTarget,
        classifier: SentimentClassifier,
) -> SentimentResult:
    if not should_classify_sentiment(
            is_valid_answer=is_valid_answer,
            answer_text=answer_text,
            mention=mention,
    ):
        return SentimentResult(
            question_id=question_id,
            mode=mode,
            target_id=target.target_id,
            classification_planned=False,
            sentiment_status=(
                "not_applicable"
            ),
        )

    provider = _classifier_name(
        classifier
    )

    try:
        raw_label = await classifier.classify(
            answer_text=answer_text,
            target=target,
        )

        label = _normalize_label(
            raw_label
        )

    except Exception as exc:
        return SentimentResult(
            question_id=question_id,
            mode=mode,
            target_id=target.target_id,
            classification_planned=True,
            sentiment_status="failed",
            provider=provider,
            reason=str(exc),
            error_type=(
                type(exc).__name__
            ),
            error_message=str(exc),
        )

    rule = apply_negative_priority_rules(
        answer_text=answer_text,
        target=target,
    )

    final_sentiment = label

    rule_override = False
    warnings: list[str] = []

    if rule.rule_hit:
        final_sentiment = "negative"

        rule_override = (
                label != "negative"
        )

        if rule_override:
            warnings.append(
                "model sentiment overridden "
                "by negative priority rule"
            )

    status = (
        "success_with_warnings"
        if rule_override
        else "success"
    )

    return SentimentResult(
        question_id=question_id,
        mode=mode,
        target_id=target.target_id,
        classification_planned=True,
        sentiment_status=status,
        model_sentiment=label,
        final_sentiment=(
            final_sentiment
        ),
        provider=provider,
        reason=rule.reason,
        evidence=list(
            rule.evidence
        ),
        rule_hit=rule.rule_hit,
        rule_override=(
            rule_override
        ),
        warnings=warnings,
    )


def _normalize_label(
        value: SentimentLabel | str,
) -> SentimentLabel:
    normalized = (
        str(value)
        .strip()
        .lower()
    )

    if normalized not in {
        "positive",
        "neutral",
        "negative",
    }:
        raise ValueError(
            "unsupported sentiment label: "
            f"{value!r}"
        )

    return normalized  # type: ignore[return-value]


def _classifier_name(
        classifier: SentimentClassifier,
) -> str:
    name = getattr(
        classifier,
        "name",
        None,
    )

    if name:
        return str(name)

    return (
        classifier
        .__class__
        .__name__
    )
