from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from app.qwen.package.exporter import (
    export_package_zip,
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


def test_export_package_zip(
        tmp_path: Path,
) -> None:
    batch_dir = (
            tmp_path
            / "batch"
    )

    batch_dir.mkdir()

    output_zip = (
            tmp_path
            / "geo_package_qwen_test.zip"
    )

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
            "关键词2",
        ],
        "sources": [
            {
                "rank": 1,
                "title": "来源一",
                "url": (
                    "https://example.com/1"
                ),
            },
            {
                "rank": 2,
                "title": "来源二",
                "url": (
                    "https://example.com/2"
                ),
            },
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

    result_path = export_package_zip(
        batch_dir=batch_dir,
        output_zip=output_zip,
        package_id=(
            "qwen-test-package"
        ),
    )

    assert result_path == output_zip

    assert output_zip.exists()

    # =========================================
    # 打开 ZIP
    # =========================================

    with zipfile.ZipFile(
            output_zip,
            "r",
    ) as zip_file:
        names = set(
            zip_file.namelist()
        )

        expected_files = {
            "manifest.json",
            "tasks.jsonl",
            "answers.jsonl",
            "sources.jsonl",
            "checksums.json",
        }

        assert (
                names
                == expected_files
        )

        # =====================================
        # manifest
        # =====================================

        manifest = json.loads(
            zip_file.read(
                "manifest.json"
            ).decode(
                "utf-8"
            )
        )

        assert (
                manifest["schema_version"]
                == "geo_batch_v1"
        )

        assert (
                manifest["platform"]
                == "qwen"
        )

        assert (
                manifest["package_id"]
                == "qwen-test-package"
        )

        assert (
                manifest["task_count"]
                == 1
        )

        assert (
                manifest["answer_count"]
                == 1
        )

        assert (
                manifest["source_count"]
                == 2
        )

        # =====================================
        # JSONL 行数
        # =====================================

        task_lines = (
            zip_file.read(
                "tasks.jsonl"
            )
            .decode(
                "utf-8"
            )
            .splitlines()
        )

        answer_lines = (
            zip_file.read(
                "answers.jsonl"
            )
            .decode(
                "utf-8"
            )
            .splitlines()
        )

        source_lines = (
            zip_file.read(
                "sources.jsonl"
            )
            .decode(
                "utf-8"
            )
            .splitlines()
        )

        assert len(
            task_lines
        ) == 1

        assert len(
            answer_lines
        ) == 1

        assert len(
            source_lines
        ) == 2

        # =====================================
        # checksums.json
        # =====================================

        checksums = json.loads(
            zip_file.read(
                "checksums.json"
            ).decode(
                "utf-8"
            )
        )

        expected_checksum_files = {
            "manifest.json",
            "tasks.jsonl",
            "answers.jsonl",
            "sources.jsonl",
        }

        assert (
                set(checksums)
                == expected_checksum_files
        )

        # 直接对 ZIP 内真实字节重新算 SHA-256
        for file_name in (
                expected_checksum_files
        ):
            actual = sha256_bytes(
                zip_file.read(
                    file_name
                )
            )

            assert (
                    checksums[file_name]
                    == actual
            )
