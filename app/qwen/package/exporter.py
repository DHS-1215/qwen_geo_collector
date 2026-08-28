from __future__ import annotations

import tempfile
import zipfile

from datetime import datetime
from pathlib import Path

from app.qwen.package.assembly import (
    assemble_package_records,
)
from app.qwen.package.models import (
    QwenPackageManifest,
)
from app.qwen.package.serialization import (
    write_json,
    write_jsonl,
)

from app.qwen.package.checksum import (
    write_checksums,
)

DATA_FILES = [
    "tasks.jsonl",
    "answers.jsonl",
    "sources.jsonl",
]

MANIFEST_FILE = "manifest.json"
CHECKSUM_FILE = "checksums.json"

PACKAGE_FILES = [
    MANIFEST_FILE,
    *DATA_FILES,
    CHECKSUM_FILE,
]

CHECKSUM_TARGET_FILES = [
    MANIFEST_FILE,
    *DATA_FILES,
]


def export_package_directory(
        *,
        batch_dir: str | Path,
        output_dir: str | Path,
        package_id: str,
) -> Path:
    batch_dir = Path(
        batch_dir
    )

    output_dir = Path(
        output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = assemble_package_records(
        batch_dir
    )

    write_jsonl(
        records.tasks,
        output_dir
        / "tasks.jsonl",
    )

    write_jsonl(
        records.answers,
        output_dir
        / "answers.jsonl",
    )

    write_jsonl(
        records.sources,
        output_dir
        / "sources.jsonl",
    )

    manifest = QwenPackageManifest(
        package_id=package_id,
        created_at=datetime.now(),
        task_count=len(
            records.tasks
        ),
        answer_count=len(
            records.answers
        ),
        source_count=len(
            records.sources
        ),
        files=PACKAGE_FILES,
    )

    write_json(
        manifest,
        output_dir
        / "manifest.json",
    )

    write_checksums(
        output_dir,
        CHECKSUM_TARGET_FILES,
    )

    return output_dir


def export_package_zip(
        *,
        batch_dir: str | Path,
        output_zip: str | Path,
        package_id: str,
) -> Path:
    output_zip = Path(
        output_zip
    )

    output_zip.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = (
                Path(temp_dir)
                / package_id
        )

        export_package_directory(
            batch_dir=batch_dir,
            output_dir=package_dir,
            package_id=package_id,
        )

        with zipfile.ZipFile(
                output_zip,
                mode="w",
                compression=(
                        zipfile.ZIP_DEFLATED
                ),
        ) as zip_file:
            for file_name in PACKAGE_FILES:
                file_path = (
                        package_dir
                        / file_name
                )

                if not file_path.exists():
                    raise FileNotFoundError(
                        "package file missing "
                        "before ZIP export: "
                        f"{file_path}"
                    )

                zip_file.write(
                    file_path,
                    arcname=file_name,
                )

    return output_zip
