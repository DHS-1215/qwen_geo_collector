from __future__ import annotations

from datetime import datetime

from app.qwen.package.models import (
    QwenPackageAnswer,
    QwenPackageManifest,
    QwenPackageSource,
    QwenPackageTask,
)


def test_package_manifest_defaults() -> None:
    manifest = QwenPackageManifest(
        package_id="qwen-test-001",
        created_at=datetime(
            2026,
            8,
            28,
            11,
            30,
        ),
        task_count=2,
        answer_count=2,
        source_count=3,
        files=[
            "tasks.jsonl",
            "answers.jsonl",
            "sources.jsonl",
            "checksums.json",
        ],
    )

    assert (
            manifest.schema_version
            == "geo_batch_v1"
    )

    assert (
            manifest.platform
            == "qwen"
    )

    assert (
            manifest.task_count
            == 2
    )

    assert (
            manifest.answer_count
            == 2
    )

    assert (
            manifest.source_count
            == 3
    )


def test_package_task_model() -> None:
    task = QwenPackageTask(
        question_id="Q001",
        question="测试问题",
        mode="quick",
        status="pass",
    )

    assert (
            task.question_id
            == "Q001"
    )

    assert (
            task.mode
            == "quick"
    )

    assert (
            task.status
            == "pass"
    )

    assert (
            task.error_type
            is None
    )


def test_package_answer_model() -> None:
    acquired_at = datetime(
        2026,
        8,
        28,
        11,
        35,
    )

    answer = QwenPackageAnswer(
        question_id="Q001",
        question="测试问题",
        mode="research",
        mode_label="思考研究",
        answer="测试回答",
        turn_id="turn-001",
        chat_url=(
            "https://www.qianwen.com/"
            "chat/test"
        ),
        search_queries=[
            "测试关键词1",
            "测试关键词2",
        ],
        citation_mapping_available=False,
        acquired_at=acquired_at,
    )

    assert (
            answer.mode
            == "research"
    )

    assert (
            answer.search_queries
            == [
                "测试关键词1",
                "测试关键词2",
            ]
    )

    assert (
            answer.citation_mapping_available
            is False
    )

    assert (
            answer.acquired_at
            == acquired_at
    )


def test_package_source_occurrence_model() -> None:
    source = QwenPackageSource(
        occurrence_id="abc123",
        question_id="Q001",
        mode="research",
        rank=1,
        title="测试来源",
        url="https://example.com/test",
    )

    assert (
            source.occurrence_id
            == "abc123"
    )

    assert (
            source.question_id
            == "Q001"
    )

    assert (
            source.rank
            == 1
    )

    assert (
            source.url
            == "https://example.com/test"
    )
