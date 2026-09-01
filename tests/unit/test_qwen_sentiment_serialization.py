from __future__ import annotations

import json
from pathlib import Path

from app.qwen.analysis.sentiment_aggregator import (
    aggregate_sentiment_results,
)
from app.qwen.analysis.sentiment_models import (
    SentimentResult,
)
from app.qwen.analysis.sentiment_serialization import (
    serialize_sentiment_metrics,
    serialize_sentiment_result,
    write_sentiment_metrics,
    write_sentiment_result,
)


def _result():
    return aggregate_sentiment_results(
        [
            SentimentResult(
                question_id="Q001",
                mode="quick",
                target_id="hongmao",
                classification_planned=True,
                sentiment_status="success",
                model_sentiment="neutral",
                final_sentiment="neutral",
            ),
            SentimentResult(
                question_id="Q001",
                mode="research",
                target_id="hongmao",
                classification_planned=True,
                sentiment_status="success",
                model_sentiment="negative",
                final_sentiment="negative",
            ),
        ]
    )


def test_serialize_sentiment_result():
    payload = (
        serialize_sentiment_result(
            _result()
        )
    )

    target = payload[
        "targets"
    ]["hongmao"]

    assert (
        target["quick"]
        ["non_negative_rate"]
        == 1.0
    )

    assert (
        target["research"]
        ["non_negative_rate"]
        == 0.0
    )

    assert (
        target["question_level"]
        ["negative_count"]
        == 1
    )

    assert len(
        payload["details"]
    ) == 2


def test_serialize_sentiment_metrics():
    payload = (
        serialize_sentiment_metrics(
            _result()
        )
    )

    rates = payload[
        "targets"
    ]["hongmao"][
        "non_negative_rate"
    ]

    assert rates == {
        "quick": 1.0,
        "research": 0.0,
        "all": 0.5,
        "question": 0.0,
    }


def test_write_sentiment_files(
    tmp_path: Path,
):
    result = _result()

    result_path = (
        write_sentiment_result(
            result,
            tmp_path
            / "sentiment_result.json",
        )
    )

    metrics_path = (
        write_sentiment_metrics(
            result,
            tmp_path
            / "sentiment_metrics.json",
        )
    )

    assert result_path.exists()
    assert metrics_path.exists()

    result_data = json.loads(
        result_path.read_text(
            encoding="utf-8"
        )
    )

    metrics_data = json.loads(
        metrics_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        result_data["targets"]
        ["hongmao"]
        ["all_answers"]
        ["classified_mention_count"]
        == 2
    )

    assert (
        metrics_data["targets"]
        ["hongmao"]
        ["negative_rate"]
        ["all"]
        == 0.5
    )
