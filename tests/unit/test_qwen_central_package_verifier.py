from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from app.qwen.package.exporter import (
    export_central_package_zip,
)
from app.qwen.package.verifier import (
    REQUIRED_FILES,
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


def _export_test_zip(tmp_path: Path, batch_dir: Path) -> Path:
    return export_central_package_zip(
        batch_dir=batch_dir,
        output_zip=tmp_path / "central.zip",
        batch_id="central-test",
        product_id="product",
        product_name="测试产品",
    )


def _read_entries(package_path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(package_path) as zip_file:
        return {name: zip_file.read(name) for name in zip_file.namelist()}


def _write_entries(package_path: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(package_path, "w") as zip_file:
        for name, data in entries.items():
            zip_file.writestr(name, data)


def _refresh_checksums(entries: dict[str, bytes]) -> None:
    entries["checksums.json"] = json.dumps({
        name: hashlib.sha256(data).hexdigest()
        for name, data in entries.items()
        if name != "checksums.json" and not name.endswith("/")
    }).encode("utf-8")


@pytest.mark.parametrize("refs", [
    ("screenshots/Q001_quick.png",),
    ("screenshots/Q001_quick.png", "screenshots/Q002_quick.png"),
    (None,), ("",), (),
])
def test_central_zip_exports_and_verifies_screenshots_or_historical_batch(
    tmp_path: Path, central_batch_factory, refs,
) -> None:
    batch_dir = central_batch_factory(refs)
    screenshot_dir = batch_dir / "screenshots"
    screenshot_dir.mkdir(exist_ok=True)
    (screenshot_dir / "orphan.png").write_bytes(b"unreferenced")
    (batch_dir / "unrelated.txt").write_text("unrelated", encoding="utf-8")
    package_path = _export_test_zip(tmp_path, batch_dir)
    entries = _read_entries(package_path)
    screenshot_refs = {ref for ref in refs if ref}
    assert set(entries) == REQUIRED_FILES | screenshot_refs
    manifest = json.loads(entries["manifest.json"])
    assert manifest["capabilities"]["supports_screenshot"] == bool(screenshot_refs)
    assert set(manifest["files"]) == REQUIRED_FILES
    verify_central_package_zip(package_path)


@pytest.mark.parametrize("wrapped_checksums", [False, True])
def test_central_verifier_ignores_directory_entries(
    tmp_path: Path, central_batch_factory, wrapped_checksums: bool,
) -> None:
    package_path = _export_test_zip(tmp_path, central_batch_factory())
    entries = _read_entries(package_path)
    entries["screenshots/"] = b""
    if wrapped_checksums:
        entries["checksums.json"] = json.dumps({
            "files": json.loads(entries["checksums.json"]),
        }).encode("utf-8")
    _write_entries(package_path, entries)
    verify_central_package_zip(package_path)


@pytest.mark.parametrize(("damage", "reason"), [
    ("missing_screenshot", "screenshot files mismatch"),
    ("missing_screenshot_checksum", "invalid checksum targets"),
    ("tampered_screenshot", "checksum mismatch: screenshots/Q001_quick.png"),
    ("unsafe_reference", "invalid central screenshot reference"),
    ("orphan_screenshot", "screenshot files mismatch"),
    ("extra_file", "invalid central screenshot reference"),
    ("extra_checksum", "invalid checksum targets"),
    ("duplicate_reference", "duplicate screenshot reference"),
    ("missing_reference", "central screenshot reference must be a string"),
    ("empty_reference", "invalid central screenshot reference"),
    ("capability_false_with_references", "without screenshot capability"),
    ("capability_false_with_files", "screenshot files mismatch"),
    ("missing_standard_file", "invalid package files"),
])
def test_central_verifier_rejects_damaged_screenshot_package(
    tmp_path: Path, central_batch_factory, damage: str, reason: str,
) -> None:
    package_path = _export_test_zip(tmp_path, central_batch_factory((
        "screenshots/Q001_quick.png", "screenshots/Q002_quick.png",
    )))
    entries = _read_entries(package_path)
    ref = "screenshots/Q001_quick.png"
    refresh_checksums = True
    if damage == "missing_screenshot":
        entries.pop(ref)
    elif damage == "missing_screenshot_checksum":
        checksums = json.loads(entries["checksums.json"])
        checksums.pop(ref)
        entries["checksums.json"] = json.dumps(checksums).encode("utf-8")
        refresh_checksums = False
    elif damage == "tampered_screenshot":
        entries[ref] += b"tampered"
        refresh_checksums = False
    elif damage == "orphan_screenshot":
        entries["screenshots/orphan.png"] = entries[ref]
    elif damage == "extra_file":
        entries["unrelated.txt"] = b"extra"
    elif damage == "extra_checksum":
        checksums = json.loads(entries["checksums.json"])
        checksums["unrelated.txt"] = "a" * 64
        entries["checksums.json"] = json.dumps(checksums).encode("utf-8")
        refresh_checksums = False
    elif damage == "missing_standard_file":
        entries.pop("sources.jsonl")
    else:
        answers = [json.loads(line) for line in
                   entries["answers.jsonl"].decode("utf-8").splitlines()]
        if damage == "unsafe_reference":
            answers[0]["screenshot_path"] = "../evil.png"
        elif damage == "duplicate_reference":
            answers[1]["screenshot_path"] = ref
        elif damage == "missing_reference":
            answers[0].pop("screenshot_path")
        elif damage == "empty_reference":
            answers[0]["screenshot_path"] = ""
        else:
            manifest = json.loads(entries["manifest.json"])
            manifest["capabilities"]["supports_screenshot"] = False
            entries["manifest.json"] = json.dumps(manifest).encode("utf-8")
            if damage == "capability_false_with_files":
                for answer in answers:
                    answer["screenshot_path"] = None
        entries["answers.jsonl"] = "".join(
            json.dumps(answer) + "\n" for answer in answers
        ).encode("utf-8")

    # Keep transport hashes valid when checking reference semantics.
    if refresh_checksums:
        _refresh_checksums(entries)
    _write_entries(package_path, entries)
    with pytest.raises(ValueError, match=reason):
        verify_central_package_zip(package_path)


def test_central_verifier_rejects_duplicate_zip_entries(
    tmp_path: Path, central_batch_factory,
) -> None:
    package_path = _export_test_zip(tmp_path, central_batch_factory())
    with zipfile.ZipFile(package_path, "a") as zip_file:
        with pytest.warns(UserWarning, match="Duplicate name"):
            zip_file.writestr("screenshots/Q001_quick.png", b"duplicate")
    with pytest.raises(ValueError, match="duplicate ZIP file entry"):
        verify_central_package_zip(package_path)


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
