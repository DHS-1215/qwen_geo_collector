from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(
        file_path: str | Path,
) -> str:
    file_path = Path(
        file_path
    )

    digest = hashlib.sha256()

    with file_path.open(
            "rb"
    ) as file:
        for chunk in iter(
                lambda: file.read(
                    1024 * 1024
                ),
                b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def build_checksums(
        package_dir: str | Path,
        files: list[str],
) -> dict[str, str]:
    package_dir = Path(
        package_dir
    )

    checksums: dict[
        str,
        str,
    ] = {}

    for file_name in files:
        file_path = (
                package_dir
                / file_name
        )

        if not file_path.exists():
            raise FileNotFoundError(
                f"package file not found: "
                f"{file_path}"
            )

        checksums[
            file_name
        ] = sha256_file(
            file_path
        )

    return checksums


def write_checksums(
        package_dir: str | Path,
        files: list[str],
) -> Path:
    package_dir = Path(
        package_dir
    )

    checksums = build_checksums(
        package_dir,
        files,
    )

    output_path = (
            package_dir
            / "checksums.json"
    )

    output_path.write_text(
        json.dumps(
            checksums,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_path
