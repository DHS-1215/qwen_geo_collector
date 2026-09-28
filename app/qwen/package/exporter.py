from __future__ import annotations

import json
import shutil
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

# =============================================
# Central GEO package export
# =============================================

from app.qwen.package.assembly import (
    assemble_central_package_records,
)
from app.qwen.package.central_models import (
    GeoPackageCapabilities,
    GeoPackageManifest,
)
from app.qwen.package.screenshot_refs import (
    validate_central_screenshot_ref,
)


CENTRAL_COLLECTOR_VERSION = (
    "qwen_geo_collector_w4.1"
)


def export_central_package_directory(
    *,
    batch_dir: str | Path,
    output_dir: str | Path,
    batch_id: str,
    product_id: str,
    product_name: str,
    collector_version: str = (
        CENTRAL_COLLECTOR_VERSION
    ),
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

    records = (
        assemble_central_package_records(
            batch_dir,
            batch_id=batch_id,
        )
    )

    screenshot_refs = []
    for answer in records.answers:
        if not answer.screenshot_path:
            continue
        ref = validate_central_screenshot_ref(answer.screenshot_path)
        if ref in screenshot_refs:
            raise ValueError(f"duplicate screenshot reference: {ref}")
        screenshot_refs.append(ref)

    if screenshot_refs and len(screenshot_refs) != len(records.answers):
        raise ValueError("partial screenshot coverage is not supported")

    for ref in screenshot_refs:
        source = batch_dir / ref
        if not source.exists():
            raise FileNotFoundError(f"screenshot file not found: {source}")
        if not source.is_file():
            raise ValueError(f"screenshot path is not a file: {source}")

    for ref in screenshot_refs:
        destination = output_dir / ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(batch_dir / ref, destination)

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

    manifest = GeoPackageManifest(
        capabilities=GeoPackageCapabilities(
            supports_screenshot=bool(screenshot_refs),
        ),
        product_id=product_id,
        product_name=product_name,
        batch_id=batch_id,
        collector_version=(
            collector_version
        ),
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
        / MANIFEST_FILE,
    )

    write_checksums(
        output_dir,
        [*CHECKSUM_TARGET_FILES, *screenshot_refs],
    )

    return output_dir


def export_central_package_zip(
    *,
    batch_dir: str | Path,
    output_zip: str | Path,
    batch_id: str,
    product_id: str,
    product_name: str,
    collector_version: str = (
        CENTRAL_COLLECTOR_VERSION
    ),
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
            / batch_id
        )

        export_central_package_directory(
            batch_dir=batch_dir,
            output_dir=package_dir,
            batch_id=batch_id,
            product_id=product_id,
            product_name=product_name,
            collector_version=(
                collector_version
            ),
        )

        package_files = list(PACKAGE_FILES)
        for line in (package_dir / "answers.jsonl").read_text(
            encoding="utf-8"
        ).splitlines():
            answer = json.loads(line)
            if answer.get("screenshot_path"):
                package_files.append(
                    validate_central_screenshot_ref(answer["screenshot_path"])
                )

        with zipfile.ZipFile(
            output_zip,
            mode="w",
            compression=(
                zipfile.ZIP_DEFLATED
            ),
        ) as zip_file:
            for file_name in package_files:
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
