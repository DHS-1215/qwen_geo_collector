from __future__ import annotations

import json
import zipfile
import hashlib
from pathlib import Path

import pytest

from app.qwen.package.exporter import (
    export_package_zip,
)
from app.qwen.package.verifier import (
    verify_package_zip,
)


def write_json(
        path: Path,
        data: dict,
) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def sha256_bytes(
        data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def build_valid_package(
        tmp_path: Path,
) -> Path:
    batch_dir = (
            tmp_path
            / "batch"
    )

    batch_dir.mkdir()

    summary = {
        "platform": "qwen",
        "status": "completed",
        "planned_count": 1,
        "executed_count": 1,
        "pass_count": 1,
        "fail_count": 0,
        "blocked_count": 0,
        "pending_count": 0,
        "task_results": [
            {
                "question_id": "Q001",
                "mode": "research",
                "question": "研究问题",
                "status": "pass",
                "output_path": (
                    "Q001_research.json"
                ),
                "error_type": None,
                "error_message": None,
            }
        ],
        "started_at": (
            "2026-08-28T13:00:00"
        ),
        "finished_at": (
            "2026-08-28T13:05:00"
        ),
    }

    write_json(
        batch_dir
        / "batch_summary.json",
        summary,
    )

    answer = {
        "platform": "qwen",
        "question_id": "Q001",
        "question": "研究问题",
        "answer": "研究回答",
        "turn_id": "turn-001",
        "chat_url": (
            "https://www.qianwen.com/"
            "chat/test"
        ),
        "mode": "research",
        "mode_label": "思考研究",
        "search_queries": [
            "关键词1",
        ],
        "sources": [
            {
                "rank": 1,
                "title": "来源一",
                "url": (
                    "https://example.com/1"
                ),
            }
        ],
        "citation_mapping_available": False,
        "acquired_at": (
            "2026-08-28T13:02:00"
        ),
    }

    write_json(
        batch_dir
        / "Q001_research.json",
        answer,
    )

    package_path = (
            tmp_path
            / "geo_package_qwen_test.zip"
    )

    export_package_zip(
        batch_dir=batch_dir,
        output_zip=package_path,
        package_id="qwen-test",
    )

    return package_path


def test_verify_valid_package(
        tmp_path: Path,
) -> None:
    package_path = (
        build_valid_package(
            tmp_path
        )
    )

    # 不抛异常即 PASS
    verify_package_zip(
        package_path
    )


def test_verify_missing_package(
        tmp_path: Path,
) -> None:
    with pytest.raises(
            FileNotFoundError,
            match="package not found",
    ):
        verify_package_zip(
            tmp_path
            / "missing.zip"
        )


def test_verify_invalid_zip(
        tmp_path: Path,
) -> None:
    package_path = (
            tmp_path
            / "bad.zip"
    )

    package_path.write_text(
        "not a zip file",
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match="invalid ZIP package",
    ):
        verify_package_zip(
            package_path
        )


def test_verify_extra_file_is_rejected(
        tmp_path: Path,
) -> None:
    package_path = (
        build_valid_package(
            tmp_path
        )
    )

    with zipfile.ZipFile(
            package_path,
            mode="a",
    ) as zip_file:
        zip_file.writestr(
            "extra.txt",
            "unexpected",
        )

    with pytest.raises(
            ValueError,
            match="invalid package files",
    ):
        verify_package_zip(
            package_path
        )


def test_verify_checksum_mismatch(
        tmp_path: Path,
) -> None:
    package_path = (
        build_valid_package(
            tmp_path
        )
    )

    # 重新制作一个 ZIP，
    # 只篡改 answers.jsonl，
    # checksums.json 保持原值
    tampered_path = (
            tmp_path
            / "tampered.zip"
    )

    with zipfile.ZipFile(
            package_path,
            "r",
    ) as source_zip:
        with zipfile.ZipFile(
                tampered_path,
                "w",
                compression=(
                        zipfile.ZIP_DEFLATED
                ),
        ) as target_zip:
            for name in (
                    source_zip.namelist()
            ):
                data = source_zip.read(
                    name
                )

                if (
                        name
                        == "answers.jsonl"
                ):
                    data = (
                        b'{"tampered":true}\n'
                    )

                target_zip.writestr(
                    name,
                    data,
                )

    with pytest.raises(
            ValueError,
            match=(
                    "checksum mismatch: "
                    "answers.jsonl"
            ),
    ):
        verify_package_zip(
            tampered_path
        )


def test_verify_manifest_count_mismatch(
        tmp_path: Path,
) -> None:
    package_path = (
        build_valid_package(
            tmp_path
        )
    )

    tampered_path = (
            tmp_path
            / "bad_count.zip"
    )

    with zipfile.ZipFile(
            package_path,
            "r",
    ) as source_zip:
        with zipfile.ZipFile(
                tampered_path,
                "w",
                compression=(
                        zipfile.ZIP_DEFLATED
                ),
        ) as target_zip:
            for name in (
                    source_zip.namelist()
            ):
                data = source_zip.read(
                    name
                )

                if name == "manifest.json":
                    manifest = json.loads(
                        data.decode(
                            "utf-8"
                        )
                    )

                    manifest[
                        "answer_count"
                    ] = 999

                    data = json.dumps(
                        manifest,
                        ensure_ascii=False,
                        indent=2,
                    ).encode(
                        "utf-8"
                    )

                target_zip.writestr(
                    name,
                    data,
                )

    with pytest.raises(
            ValueError,
            match="checksum mismatch: manifest.json",
    ):
        verify_package_zip(
            tampered_path
        )


def test_verify_unsupported_schema_version(
        tmp_path: Path,
) -> None:
    package_path = (
        build_valid_package(
            tmp_path
        )
    )

    tampered_path = (
            tmp_path
            / "bad_schema.zip"
    )

    with zipfile.ZipFile(
            package_path,
            "r",
    ) as source_zip:
        original_files = {
            name: source_zip.read(name)
            for name
            in source_zip.namelist()
        }

    manifest = json.loads(
        original_files[
            "manifest.json"
        ].decode(
            "utf-8"
        )
    )

    manifest[
        "schema_version"
    ] = "geo_batch_v999"

    manifest_bytes = json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
    ).encode(
        "utf-8"
    )

    original_files[
        "manifest.json"
    ] = manifest_bytes

    checksums = json.loads(
        original_files[
            "checksums.json"
        ].decode(
            "utf-8"
        )
    )

    checksums[
        "manifest.json"
    ] = sha256_bytes(
        manifest_bytes
    )

    original_files[
        "checksums.json"
    ] = json.dumps(
        checksums,
        ensure_ascii=False,
        indent=2,
    ).encode(
        "utf-8"
    )

    with zipfile.ZipFile(
            tampered_path,
            "w",
            compression=(
                    zipfile.ZIP_DEFLATED
            ),
    ) as target_zip:
        for name, data in (
                original_files.items()
        ):
            target_zip.writestr(
                name,
                data,
            )

    with pytest.raises(
            ValueError,
            match=(
                    "unsupported schema version"
            ),
    ):
        verify_package_zip(
            tampered_path
        )


def test_verify_invalid_jsonl(
        tmp_path: Path,
) -> None:
    package_path = (
        build_valid_package(
            tmp_path
        )
    )

    tampered_path = (
            tmp_path
            / "bad_jsonl.zip"
    )

    with zipfile.ZipFile(
            package_path,
            "r",
    ) as source_zip:
        original_files = {
            name: source_zip.read(name)
            for name
            in source_zip.namelist()
        }

    bad_answers = (
        b'{"broken":\n'
    )

    original_files[
        "answers.jsonl"
    ] = bad_answers

    checksums = json.loads(
        original_files[
            "checksums.json"
        ].decode(
            "utf-8"
        )
    )

    checksums[
        "answers.jsonl"
    ] = sha256_bytes(
        bad_answers
    )

    original_files[
        "checksums.json"
    ] = json.dumps(
        checksums,
        ensure_ascii=False,
        indent=2,
    ).encode(
        "utf-8"
    )

    with zipfile.ZipFile(
            tampered_path,
            "w",
            compression=(
                    zipfile.ZIP_DEFLATED
            ),
    ) as target_zip:
        for name, data in (
                original_files.items()
        ):
            target_zip.writestr(
                name,
                data,
            )

    with pytest.raises(
            ValueError,
            match="invalid JSONL",
    ):
        verify_package_zip(
            tampered_path
        )
