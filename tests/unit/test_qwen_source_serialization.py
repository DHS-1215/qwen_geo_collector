from __future__ import annotations

import json
from pathlib import Path

from app.qwen.analysis.source_aggregator import (
    aggregate_source_occurrences,
)
from app.qwen.analysis.source_models import (
    SourceOccurrence,
)
from app.qwen.analysis.source_serialization import (
    serialize_source_metrics,
    serialize_source_result,
    write_source_metrics,
    write_source_result,
)


def _result():
    return aggregate_source_occurrences(
        [
            SourceOccurrence(
                question_id="Q001",
                mode="quick",
                source_key=(
                    "https://example.com/a"
                ),
                domain="example.com",
                title="A",
                url=(
                    "https://example.com/a"
                ),
                rank=1,
            ),
            SourceOccurrence(
                question_id="Q002",
                mode="quick",
                source_key=(
                    "https://example.com/b"
                ),
                domain="example.com",
                title="B",
                url=(
                    "https://example.com/b"
                ),
                rank=2,
            ),
            SourceOccurrence(
                question_id="Q001",
                mode="research",
                source_key=(
                    "https://other.com/a"
                ),
                domain="other.com",
                title="C",
                url=(
                    "https://other.com/a"
                ),
                rank=1,
            ),
        ]
    )


def test_serialize_source_result():
    payload = (
        serialize_source_result(
            _result()
        )
    )

    assert (
        payload["url_level"]
        ["quick"]
        ["total_occurrences"]
        == 2
    )

    assert (
        payload["host_level"]
        ["quick"]
        ["unique_host_count"]
        == 1
    )

    assert (
        len(
            payload["occurrences"]
        )
        == 3
    )


def test_serialize_source_metrics():
    payload = (
        serialize_source_metrics(
            _result()
        )
    )

    assert (
        payload[
            "source_occurrences"
        ]["all"]
        == 3
    )

    assert (
        payload[
            "unique_sources"
        ]["all"]
        == 3
    )

    assert (
        payload[
            "unique_hosts"
        ]["all"]
        == 2
    )

    assert (
        payload[
            "source_top10_share"
        ]["all"]
        == 1.0
    )

    assert (
        payload[
            "host_top10_share"
        ]["all"]
        == 1.0
    )


def test_write_source_files(
    tmp_path: Path,
):
    result = _result()

    result_path = (
        write_source_result(
            result,
            tmp_path
            / "source_result.json",
        )
    )

    metrics_path = (
        write_source_metrics(
            result,
            tmp_path
            / "source_metrics.json",
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
        result_data["url_level"]
        ["all"]
        ["total_occurrences"]
        == 3
    )

    assert (
        metrics_data[
            "unique_hosts"
        ]["quick"]
        == 1
    )
