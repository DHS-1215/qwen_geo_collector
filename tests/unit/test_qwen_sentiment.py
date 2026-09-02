from __future__ import annotations

import asyncio

from app.qwen.analysis.mention import (
    analyze_target,
)
from app.qwen.analysis.models import (
    MentionTarget,
)
from app.qwen.analysis.sentiment import (
    analyze_sentiment,
    should_classify_sentiment,
)


class FakeClassifier:
    name = "fake-classifier"

    def __init__(
        self,
        result: str,
    ) -> None:
        self.result = result
        self.call_count = 0

    async def classify(
        self,
        *,
        answer_text: str,
        target: MentionTarget,
    ) -> str:
        self.call_count += 1
        return self.result


class FailingClassifier:
    name = "failing-classifier"

    async def classify(
        self,
        *,
        answer_text: str,
        target: MentionTarget,
    ) -> str:
        raise RuntimeError(
            "classifier failed"
        )


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao",
        aliases=[
            "鸿茅药酒",
        ],
    )


def test_should_classify_when_mentioned():
    answer = "鸿茅药酒是正规药品。"

    mention = analyze_target(
        answer,
        _target(),
    )

    assert should_classify_sentiment(
        is_valid_answer=True,
        answer_text=answer,
        mention=mention,
    )


def test_should_not_classify_without_mention():
    answer = "这是普通回答。"

    mention = analyze_target(
        answer,
        _target(),
    )

    assert not should_classify_sentiment(
        is_valid_answer=True,
        answer_text=answer,
        mention=mention,
    )


def test_should_not_classify_invalid_answer():
    answer = "鸿茅药酒。"

    mention = analyze_target(
        answer,
        _target(),
    )

    assert not should_classify_sentiment(
        is_valid_answer=False,
        answer_text=answer,
        mention=mention,
    )


def test_positive_sentiment():
    answer = "鸿茅药酒整体表现不错。"

    classifier = FakeClassifier(
        "positive"
    )

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q001",
            mode="quick",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
        result.sentiment_status
        == "success"
    )

    assert (
        result.model_sentiment
        == "positive"
    )

    assert (
        result.final_sentiment
        == "positive"
    )

    assert (
        result.provider
        == "fake-classifier"
    )

    assert classifier.call_count == 1


def test_neutral_sentiment():
    answer = "鸿茅药酒属于一种药品。"

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q001",
            mode="quick",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=FakeClassifier(
                "NEUTRAL"
            ),
        )
    )

    assert (
        result.final_sentiment
        == "neutral"
    )


def test_negative_sentiment():
    answer = "鸿茅药酒存在负面争议。"

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q001",
            mode="research",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=FakeClassifier(
                "negative"
            ),
        )
    )

    assert (
        result.final_sentiment
        == "negative"
    )


def test_not_mentioned_is_not_applicable():
    answer = "这是普通回答。"

    classifier = FakeClassifier(
        "positive"
    )

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q001",
            mode="quick",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
        result.sentiment_status
        == "not_applicable"
    )

    assert (
        result.classification_planned
        is False
    )

    assert (
        result.final_sentiment
        is None
    )

    assert classifier.call_count == 0


def test_invalid_answer_is_not_applicable():
    answer = "鸿茅药酒。"

    classifier = FakeClassifier(
        "positive"
    )

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q001",
            mode="quick",
            answer_text=answer,
            is_valid_answer=False,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
        result.sentiment_status
        == "not_applicable"
    )

    assert classifier.call_count == 0


def test_classifier_failure_returns_failed():
    answer = "鸿茅药酒是药品。"

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q001",
            mode="quick",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=(
                FailingClassifier()
            ),
        )
    )

    assert (
        result.sentiment_status
        == "failed"
    )

    assert (
        result.final_sentiment
        is None
    )

    assert (
        result.provider
        == "failing-classifier"
    )

    assert (
        result.error_type
        == "RuntimeError"
    )

    assert (
        result.reason
        == "classifier failed"
    )


def test_invalid_classifier_label_returns_failed():
    answer = "鸿茅药酒是药品。"

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q001",
            mode="quick",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=FakeClassifier(
                "unknown"
            ),
        )
    )

    assert (
        result.sentiment_status
        == "failed"
    )

    assert (
        result.final_sentiment
        is None
    )

    assert (
        "unsupported sentiment label"
        in (result.reason or "")
    )


def test_business_rule_overrides_positive_model():
    answer = (
        "鸿茅药酒曾因违法广告"
        "引发监管争议。"
    )

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q008",
            mode="quick",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=FakeClassifier(
                "positive"
            ),
        )
    )

    assert (
        result.model_sentiment
        == "positive"
    )

    assert (
        result.final_sentiment
        == "negative"
    )

    assert result.rule_hit
    assert result.rule_override

    assert (
        result.sentiment_status
        == "success_with_warnings"
    )


def test_business_rule_does_not_override_negative_model():
    answer = (
        "鸿茅药酒曾涉及虚假宣传。"
    )

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q008",
            mode="research",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=FakeClassifier(
                "negative"
            ),
        )
    )

    assert (
        result.model_sentiment
        == "negative"
    )

    assert (
        result.final_sentiment
        == "negative"
    )

    assert result.rule_hit

    assert (
        result.rule_override
        is False
    )

    assert (
        result.sentiment_status
        == "success"
    )


def test_negated_rule_keeps_model_sentiment():
    answer = (
        "没有证据表明鸿茅药酒"
        "存在虚假宣传。"
    )

    result = asyncio.run(
        analyze_sentiment(
            question_id="Q008",
            mode="quick",
            answer_text=answer,
            is_valid_answer=True,
            mention=analyze_target(
                answer,
                _target(),
            ),
            target=_target(),
            classifier=FakeClassifier(
                "neutral"
            ),
        )
    )

    assert (
        result.model_sentiment
        == "neutral"
    )

    assert (
        result.final_sentiment
        == "neutral"
    )

    assert not result.rule_hit
    assert not result.rule_override
