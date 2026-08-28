from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.qwen.package.checksum import (
    build_checksums,
    sha256_file,
    write_checksums,
)


def test_sha256_file(
        tmp_path: Path,
) -> None:
    file_path = (
            tmp_path
            / "sample.txt"
    )

    content = b"hello qwen"

    file_path.write_bytes(
        content
    )

    expected = hashlib.sha256(
        content
    ).hexdigest()

    actual = sha256_file(
        file_path
    )

    assert actual == expected


def test_build_checksums(
        tmp_path: Path,
) -> None:
    tasks_path = (
            tmp_path
            / "tasks.jsonl"
    )

    answers_path = (
            tmp_path
            / "answers.jsonl"
    )

    tasks_path.write_text(
        '{"question_id":"Q001"}\n',
        encoding="utf-8",
    )

    answers_path.write_text(
        '{"answer":"测试回答"}\n',
        encoding="utf-8",
    )

    checksums = build_checksums(
        tmp_path,
        [
            "tasks.jsonl",
            "answers.jsonl",
        ],
    )

    assert set(
        checksums
    ) == {
               "tasks.jsonl",
               "answers.jsonl",
           }

    assert (
            checksums["tasks.jsonl"]
            == sha256_file(
        tasks_path
    )
    )

    assert (
            checksums["answers.jsonl"]
            == sha256_file(
        answers_path
    )
    )


def test_write_checksums(
        tmp_path: Path,
) -> None:
    (
            tmp_path
            / "tasks.jsonl"
    ).write_text(
        "task-data\n",
        encoding="utf-8",
    )

    (
            tmp_path
            / "answers.jsonl"
    ).write_text(
        "answer-data\n",
        encoding="utf-8",
    )

    output_path = write_checksums(
        tmp_path,
        [
            "tasks.jsonl",
            "answers.jsonl",
        ],
    )

    assert (
            output_path
            == tmp_path
            / "checksums.json"
    )

    assert output_path.exists()

    data = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
            data["tasks.jsonl"]
            == sha256_file(
        tmp_path
        / "tasks.jsonl"
    )
    )

    assert (
            data["answers.jsonl"]
            == sha256_file(
        tmp_path
        / "answers.jsonl"
    )
    )


def test_build_checksums_missing_file(
        tmp_path: Path,
) -> None:
    with pytest.raises(
            FileNotFoundError,
            match="package file not found",
    ):
        build_checksums(
            tmp_path,
            [
                "missing.jsonl",
            ],
        )
