from __future__ import annotations

from app.qwen.analysis.models import (
    MentionBatchResult,
    MentionDetail,
    MentionSummary,
    TargetMentionSummary,
)
from app.qwen.analysis.serialization import (
    serialize_mention_metrics,
    serialize_mention_result,
)


def make_result() -> MentionBatchResult:
    return MentionBatchResult(
        details=[
            MentionDetail(
                question_id="Q001",
                mode="quick",
                target_id="hongmao",
                mention_count=2,
                mentioned=True,
            ),
            MentionDetail(
                question_id="Q001",
                mode="research",
                target_id="hongmao",
                mention_count=0,
                mentioned=False,
            ),
        ],
        summaries={
            "hongmao": TargetMentionSummary(
                target_id="hongmao",
                quick=MentionSummary(
                    valid_count=2,
                    mentioned_count=1,
                    mention_rate=0.5,
                ),
                research=MentionSummary(
                    valid_count=1,
                    mentioned_count=1,
                    mention_rate=1.0,
                ),
                all_answers=MentionSummary(
                    valid_count=3,
                    mentioned_count=2,
                    mention_rate=2 / 3,
                ),
                question_level=MentionSummary(
                    valid_count=2,
                    mentioned_count=1,
                    mention_rate=0.5,
                ),
            )
        },
    )


def test_serialize_mention_result() -> None:
    document = serialize_mention_result(
        make_result()
    )

    target = document["targets"][
        "hongmao"
    ]

    assert target["quick"] == {
        "valid_count": 2,
        "mentioned_count": 1,
        "mention_rate": 0.5,
    }

    assert target["research"][
        "mention_rate"
    ] == 1.0

    assert target["all_answers"][
        "valid_count"
    ] == 3

    assert target["question_level"][
        "mention_rate"
    ] == 0.5


def test_serialize_mention_details() -> None:
    document = serialize_mention_result(
        make_result()
    )

    assert len(document["details"]) == 2

    first = document["details"][0]

    assert first["question_id"] == "Q001"
    assert first["mode"] == "quick"
    assert first["target_id"] == "hongmao"
    assert first["mention_count"] == 2
    assert first["mentioned"] is True


def test_serialize_mention_metrics_uses_compact_names() -> None:
    metrics = serialize_mention_metrics(
        make_result()
    )

    mention_rate = metrics["targets"][
        "hongmao"
    ]["mention_rate"]

    assert mention_rate == {
        "quick": 0.5,
        "research": 1.0,
        "all": 2 / 3,
        "question": 0.5,
    }

    assert "all_answers" not in mention_rate
    assert "question_level" not in mention_rate
