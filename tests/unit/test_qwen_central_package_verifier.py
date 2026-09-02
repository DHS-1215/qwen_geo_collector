from __future__ import annotations

from pathlib import Path

import pytest

from app.qwen.package.exporter import (
    export_central_package_zip,
)
from app.qwen.package.verifier import (
    verify_central_package_zip,
)


def test_verify_real_central_package(
    tmp_path: Path,
) -> None:
    batch_dir = Path(
        "output/w3_baseline_16"
    )

    if not batch_dir.exists():
        pytest.skip(
            "real W3 baseline not available"
        )

    package_path = (
        tmp_path
        / "qwen-central.zip"
    )

    export_central_package_zip(
        batch_dir=batch_dir,
        output_zip=package_path,
        batch_id="qwen-test-central",
        product_id="hongmao",
        product_name="鸿茅药酒",
    )

    verify_central_package_zip(
        package_path
    )


def test_existing_central_validation_package(
) -> None:
    package_path = Path(
        "output/"
        "qwen_w4_central_validation.zip"
    )

    if not package_path.exists():
        pytest.skip(
            "central validation package "
            "not available"
        )

    verify_central_package_zip(
        package_path
    )
