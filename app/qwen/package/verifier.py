from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from app.qwen.package.models import (
    QwenPackageManifest,
)

REQUIRED_FILES = {
    "manifest.json",
    "tasks.jsonl",
    "answers.jsonl",
    "sources.jsonl",
    "checksums.json",
}


def sha256_bytes(
        data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def read_jsonl_bytes(
        data: bytes,
        *,
        file_name: str,
) -> list[dict]:
    text = data.decode(
        "utf-8"
    )

    records: list[dict] = []

    for line_number, line in enumerate(
            text.splitlines(),
            start=1,
    ):
        if not line.strip():
            continue

        try:
            record = json.loads(
                line
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "invalid JSONL: "
                f"{file_name}, "
                f"line={line_number}"
            ) from exc

        records.append(
            record
        )

    return records


def verify_package_zip(
        package_path: str | Path,
) -> None:
    package_path = Path(
        package_path
    )

    if not package_path.exists():
        raise FileNotFoundError(
            f"package not found: "
            f"{package_path}"
        )

    if not zipfile.is_zipfile(
            package_path
    ):
        raise ValueError(
            f"invalid ZIP package: "
            f"{package_path}"
        )

    with zipfile.ZipFile(
            package_path,
            "r",
    ) as zip_file:
        names = set(
            zip_file.namelist()
        )

        if names != REQUIRED_FILES:
            missing = (
                    REQUIRED_FILES
                    - names
            )

            extra = (
                    names
                    - REQUIRED_FILES
            )

            raise ValueError(
                "invalid package files; "
                f"missing={sorted(missing)}, "
                f"extra={sorted(extra)}"
            )

        try:
            manifest_data = json.loads(
                zip_file.read(
                    "manifest.json"
                ).decode(
                    "utf-8"
                )
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "invalid manifest JSON"
            ) from exc

        try:
            manifest = QwenPackageManifest(
                **manifest_data
            )

        except Exception as exc:
            raise ValueError(
                "invalid manifest schema"
            ) from exc

        if (
                manifest.schema_version
                != "geo_batch_v1"
        ):
            raise ValueError(
                "unsupported schema version: "
                f"{manifest.schema_version}"
            )

        if manifest.platform != "qwen":
            raise ValueError(
                "invalid package platform: "
                f"{manifest.platform}"
            )

        if set(
                manifest.files
        ) != REQUIRED_FILES:
            raise ValueError(
                "manifest files mismatch"
            )

        checksums = json.loads(
            zip_file.read(
                "checksums.json"
            ).decode(
                "utf-8"
            )
        )

        tasks = read_jsonl_bytes(
            zip_file.read(
                "tasks.jsonl"
            ),
            file_name="tasks.jsonl",
        )

        answers = read_jsonl_bytes(
            zip_file.read(
                "answers.jsonl"
            ),
            file_name="answers.jsonl",
        )

        sources = read_jsonl_bytes(
            zip_file.read(
                "sources.jsonl"
            ),
            file_name="sources.jsonl",
        )

        checksum_targets = {
            "manifest.json",
            "tasks.jsonl",
            "answers.jsonl",
            "sources.jsonl",
        }

        if (
                set(checksums)
                != checksum_targets
        ):
            raise ValueError(
                "invalid checksum targets"
            )

        for file_name in (
                checksum_targets
        ):
            actual = sha256_bytes(
                zip_file.read(
                    file_name
                )
            )

            expected = checksums[
                file_name
            ]

            if actual != expected:
                raise ValueError(
                    "checksum mismatch: "
                    f"{file_name}"
                )

        tasks = read_jsonl_bytes(
            zip_file.read(
                "tasks.jsonl"
            ),
            file_name="tasks.jsonl",
        )

        answers = read_jsonl_bytes(
            zip_file.read(
                "answers.jsonl"
            ),
            file_name="answers.jsonl",
        )

        sources = read_jsonl_bytes(
            zip_file.read(
                "sources.jsonl"
            ),
            file_name="sources.jsonl",
        )

        if len(tasks) != manifest.task_count:
            raise ValueError(
                "task count mismatch: "
                f"manifest={manifest.task_count}, "
                f"actual={len(tasks)}"
            )

        if len(answers) != manifest.answer_count:
            raise ValueError(
                "answer count mismatch: "
                f"manifest={manifest.answer_count}, "
                f"actual={len(answers)}"
            )

        if len(sources) != manifest.source_count:
            raise ValueError(
                "source count mismatch: "
                f"manifest={manifest.source_count}, "
                f"actual={len(sources)}"
            )

# =============================================
# Central GEO package verification
# =============================================

from app.qwen.package.central_models import (
    GeoPackageAnswer,
    GeoPackageManifest,
    GeoPackageSource,
    GeoPackageTask,
)


CENTRAL_FORBIDDEN_ANALYSIS_FIELDS = {
    "mention",
    "sentiment",
    "metrics",
    "metric_result",
}


def verify_central_package_zip(
    package_path: str | Path,
) -> None:
    package_path = Path(
        package_path
    )

    if not package_path.exists():
        raise FileNotFoundError(
            f"package not found: "
            f"{package_path}"
        )

    if not zipfile.is_zipfile(
        package_path
    ):
        raise ValueError(
            f"invalid ZIP package: "
            f"{package_path}"
        )

    with zipfile.ZipFile(
        package_path,
        "r",
    ) as zip_file:
        names = set(
            zip_file.namelist()
        )

        if names != REQUIRED_FILES:
            missing = (
                REQUIRED_FILES
                - names
            )

            extra = (
                names
                - REQUIRED_FILES
            )

            raise ValueError(
                "invalid package files; "
                f"missing={sorted(missing)}, "
                f"extra={sorted(extra)}"
            )

        try:
            manifest_data = json.loads(
                zip_file.read(
                    "manifest.json"
                ).decode(
                    "utf-8"
                )
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "invalid manifest JSON"
            ) from exc

        try:
            manifest = (
                GeoPackageManifest(
                    **manifest_data
                )
            )

        except Exception as exc:
            raise ValueError(
                "invalid central manifest schema"
            ) from exc

        if (
            manifest.schema_version
            != "geo_package_v1"
        ):
            raise ValueError(
                "unsupported schema version: "
                f"{manifest.schema_version}"
            )

        if (
            manifest.geo_batch_version
            != "geo_batch_v1"
        ):
            raise ValueError(
                "unsupported geo batch version: "
                f"{manifest.geo_batch_version}"
            )

        if (
            manifest.platform_code
            != "qwen"
        ):
            raise ValueError(
                "invalid package platform: "
                f"{manifest.platform_code}"
            )

        if set(
            manifest.files
        ) != REQUIRED_FILES:
            raise ValueError(
                "manifest files mismatch"
            )

        try:
            checksums = json.loads(
                zip_file.read(
                    "checksums.json"
                ).decode(
                    "utf-8"
                )
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "invalid checksums JSON"
            ) from exc

        checksum_targets = {
            "manifest.json",
            "tasks.jsonl",
            "answers.jsonl",
            "sources.jsonl",
        }

        checksum_files = (
            checksums.get(
                "files",
                checksums,
            )
            if isinstance(
                checksums,
                dict,
            )
            else None
        )

        if not isinstance(
            checksum_files,
            dict,
        ):
            raise ValueError(
                "invalid checksum structure"
            )

        if (
            set(checksum_files)
            != checksum_targets
        ):
            raise ValueError(
                "invalid checksum targets"
            )

        for file_name in checksum_targets:
            actual = sha256_bytes(
                zip_file.read(
                    file_name
                )
            )

            expected = checksum_files[
                file_name
            ]

            if actual != expected:
                raise ValueError(
                    "checksum mismatch: "
                    f"{file_name}"
                )

        task_dicts = read_jsonl_bytes(
            zip_file.read(
                "tasks.jsonl"
            ),
            file_name="tasks.jsonl",
        )

        answer_dicts = read_jsonl_bytes(
            zip_file.read(
                "answers.jsonl"
            ),
            file_name="answers.jsonl",
        )

        source_dicts = read_jsonl_bytes(
            zip_file.read(
                "sources.jsonl"
            ),
            file_name="sources.jsonl",
        )

        try:
            tasks = [
                GeoPackageTask(
                    **record
                )
                for record
                in task_dicts
            ]

            answers = [
                GeoPackageAnswer(
                    **record
                )
                for record
                in answer_dicts
            ]

            sources = [
                GeoPackageSource(
                    **record
                )
                for record
                in source_dicts
            ]

        except Exception as exc:
            raise ValueError(
                "invalid central package "
                "JSONL schema"
            ) from exc

        if (
            len(tasks)
            != manifest.task_count
        ):
            raise ValueError(
                "task count mismatch: "
                f"manifest={manifest.task_count}, "
                f"actual={len(tasks)}"
            )

        if (
            len(answers)
            != manifest.answer_count
        ):
            raise ValueError(
                "answer count mismatch: "
                f"manifest={manifest.answer_count}, "
                f"actual={len(answers)}"
            )

        if (
            len(sources)
            != manifest.source_count
        ):
            raise ValueError(
                "source count mismatch: "
                f"manifest={manifest.source_count}, "
                f"actual={len(sources)}"
            )

        task_ids = {
            task.task_id
            for task in tasks
        }

        if (
            len(task_ids)
            != len(tasks)
        ):
            raise ValueError(
                "duplicate task_id"
            )

        answer_ids = {
            answer.answer_id
            for answer in answers
        }

        if (
            len(answer_ids)
            != len(answers)
        ):
            raise ValueError(
                "duplicate answer_id"
            )

        occurrence_ids = {
            source.occurrence_id
            for source in sources
        }

        if (
            len(occurrence_ids)
            != len(sources)
        ):
            raise ValueError(
                "duplicate occurrence_id"
            )

        for answer in answers:
            if (
                answer.task_id
                not in task_ids
            ):
                raise ValueError(
                    "answer references "
                    "missing task: "
                    f"{answer.answer_id}"
                )

        for source in sources:
            if (
                source.answer_id
                not in answer_ids
            ):
                raise ValueError(
                    "source references "
                    "missing answer: "
                    f"{source.occurrence_id}"
                )

        for record in answer_dicts:
            forbidden = (
                CENTRAL_FORBIDDEN_ANALYSIS_FIELDS
                & set(record)
            )

            if forbidden:
                raise ValueError(
                    "answer contains forbidden "
                    "analysis fields: "
                    f"{sorted(forbidden)}"
                )

            platform_meta = (
                record.get(
                    "platform_meta_json"
                )
                or {}
            )

            if not isinstance(
                platform_meta,
                dict,
            ):
                raise ValueError(
                    "platform_meta_json "
                    "must be an object"
                )

            forbidden_meta = (
                CENTRAL_FORBIDDEN_ANALYSIS_FIELDS
                & set(platform_meta)
            )

            if forbidden_meta:
                raise ValueError(
                    "platform_meta_json contains "
                    "forbidden analysis fields: "
                    f"{sorted(forbidden_meta)}"
                )
