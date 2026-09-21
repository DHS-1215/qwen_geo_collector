from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from app.qwen.answer_cleaning import (
    clean_qwen_answer_text,
)
from app.qwen.package.site_utils import (
    source_site_name_from_url,
)
from app.qwen.service_busy import (
    is_qwen_service_busy,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"


def read_jsonl(
    path: Path,
) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(
            encoding="utf-8-sig"
        ).splitlines()
        if line.strip()
    ]


def write_jsonl(
    path: Path,
    rows: list[dict],
) -> None:
    path.write_text(
        "".join(
            json.dumps(
                row,
                ensure_ascii=False,
            )
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def main() -> None:
    candidates = [
        path
        for path in OUTPUT.glob(
            "qwen_geo_*.zip"
        )
        if "_repaired" not in path.stem
        and "_before_repair" not in path.stem
    ]

    if not candidates:
        raise FileNotFoundError(
            "No original qwen_geo_*.zip found"
        )

    source_zip = max(
        candidates,
        key=lambda p: p.stat().st_mtime,
    )

    backup_zip = source_zip.with_name(
        source_zip.stem
        + "_before_repair.zip"
    )

    repaired_zip = source_zip.with_name(
        source_zip.stem
        + "_repaired.zip"
    )

    print(
        "[SOURCE]",
        source_zip,
    )

    if not backup_zip.exists():
        shutil.copy2(
            source_zip,
            backup_zip,
        )

    print(
        "[BACKUP]",
        backup_zip,
    )

    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)

        with zipfile.ZipFile(
            source_zip
        ) as zf:
            zf.extractall(work)

        manifest_path = work / "manifest.json"
        tasks_path = work / "tasks.jsonl"
        answers_path = work / "answers.jsonl"
        sources_path = work / "sources.jsonl"
        checksums_path = work / "checksums.json"

        manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8-sig"
            )
        )

        tasks = read_jsonl(
            tasks_path
        )
        answers = read_jsonl(
            answers_path
        )
        sources = read_jsonl(
            sources_path
        )

        invalid_answer_ids: set[str] = set()
        invalid_task_ids: set[str] = set()

        for answer in answers:
            raw = (
                answer.get(
                    "answer_text_raw"
                )
                or ""
            )

            if not is_qwen_service_busy(
                raw
            ):
                continue

            invalid_answer_ids.add(
                answer["answer_id"]
            )
            invalid_task_ids.add(
                answer["task_id"]
            )

            print(
                "[INVALID SERVICE BUSY]",
                answer["question_id"],
                answer["mode_code"],
                repr(raw),
            )

        for task in tasks:
            if (
                task["task_id"]
                not in invalid_task_ids
            ):
                continue

            task["task_status"] = "failed"
            task["error_code"] = (
                "QwenServiceBusyError"
            )
            task["error_message"] = (
                "Qwen returned a temporary "
                "service-busy system message."
            )

        answers = [
            answer
            for answer in answers
            if answer["answer_id"]
            not in invalid_answer_ids
        ]

        sources = [
            source
            for source in sources
            if source["answer_id"]
            not in invalid_answer_ids
        ]

        quick_cleaned = 0

        for answer in answers:
            if (
                answer.get("mode_code")
                != "quick"
            ):
                continue

            raw = (
                answer.get(
                    "answer_text_raw"
                )
                or answer.get(
                    "answer_text_clean"
                )
                or ""
            )

            cleaned = (
                clean_qwen_answer_text(
                    raw,
                    mode="quick",
                )
            )

            if (
                cleaned
                != (
                    answer.get(
                        "answer_text_clean"
                    )
                    or ""
                ).strip()
            ):
                answer[
                    "answer_text_clean"
                ] = cleaned

                quick_cleaned += 1

        site_fixed = 0

        for source in sources:
            if source.get(
                "source_site_name_raw"
            ):
                continue

            site = (
                source_site_name_from_url(
                    source.get(
                        "source_url_raw"
                    )
                )
            )

            if site:
                source[
                    "source_site_name_raw"
                ] = site

                site_fixed += 1

        manifest["task_count"] = len(
            tasks
        )
        manifest["answer_count"] = len(
            answers
        )
        manifest["source_count"] = len(
            sources
        )

        # Keep status / timestamps unchanged.
        # Existing geo_package_v1 packages currently
        # use null for these fields.

        manifest_path.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        write_jsonl(
            tasks_path,
            tasks,
        )

        write_jsonl(
            answers_path,
            answers,
        )

        write_jsonl(
            sources_path,
            sources,
        )

        checksums = {
            "manifest.json":
                sha256(manifest_path),
            "tasks.jsonl":
                sha256(tasks_path),
            "answers.jsonl":
                sha256(answers_path),
            "sources.jsonl":
                sha256(sources_path),
        }

        checksums_path.write_text(
            json.dumps(
                checksums,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        # --------------------------------------------
        # Integrity checks before creating ZIP
        # --------------------------------------------

        task_ids = {
            task["task_id"]
            for task in tasks
        }

        answer_ids = {
            answer["answer_id"]
            for answer in answers
        }

        assert len(
            answer_ids
        ) == len(
            answers
        )

        assert all(
            answer["task_id"]
            in task_ids
            for answer in answers
        )

        assert all(
            source["answer_id"]
            in answer_ids
            for source in sources
        )

        source_count_by_answer: dict[
            str,
            int,
        ] = {}

        for source in sources:
            source_count_by_answer[
                source["answer_id"]
            ] = (
                source_count_by_answer.get(
                    source["answer_id"],
                    0,
                )
                + 1
            )

        for answer in answers:
            assert (
                source_count_by_answer.get(
                    answer["answer_id"],
                    0,
                )
                == answer[
                    "source_count_raw"
                ]
            )

        assert manifest[
            "task_count"
        ] == len(tasks)

        assert manifest[
            "answer_count"
        ] == len(answers)

        assert manifest[
            "source_count"
        ] == len(sources)

        with zipfile.ZipFile(
            repaired_zip,
            "w",
            compression=(
                zipfile.ZIP_DEFLATED
            ),
        ) as zf:
            for name in (
                "manifest.json",
                "tasks.jsonl",
                "answers.jsonl",
                "sources.jsonl",
                "checksums.json",
            ):
                zf.write(
                    work / name,
                    arcname=name,
                )

    failed_tasks = [
        task
        for task in tasks
        if task.get(
            "task_status"
        ) != "success"
    ]

    print()
    print(
        "[REPAIRED]",
        repaired_zip,
    )
    print(
        "[INVALID ANSWERS]",
        len(invalid_answer_ids),
    )
    print(
        "[QUICK CLEANED]",
        quick_cleaned,
    )
    print(
        "[SITE NAME FIXED]",
        site_fixed,
    )
    print(
        "[FINAL]",
        f"tasks={len(tasks)}",
        f"answers={len(answers)}",
        f"sources={len(sources)}",
        f"failed={len(failed_tasks)}",
    )


if __name__ == "__main__":
    main()
