from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.qwen.package.exporter import (
    CHECKSUM_TARGET_FILES,
    PACKAGE_FILES,
    export_central_package_directory,
)
from app.qwen.package.screenshot_refs import validate_central_screenshot_ref


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


def test_export_central_package_directory(
    tmp_path: Path,
) -> None:
    batch_dir = (
        tmp_path
        / "batch"
    )

    package_dir = (
        tmp_path
        / "package"
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
            "2026-09-01T12:00:00"
        ),
        "finished_at": (
            "2026-09-01T12:05:00"
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
        "search_queries": [],
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
            "2026-09-01T12:02:00"
        ),
    }

    write_json(
        batch_dir
        / "Q001_research.json",
        answer,
    )

    export_central_package_directory(
        batch_dir=batch_dir,
        output_dir=package_dir,
        batch_id="qwen-central-test",
        product_id="hongmao",
        product_name="鸿茅药酒",
    )

    manifest = json.loads(
        (
            package_dir
            / "manifest.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest["schema_version"]
        == "geo_package_v1"
    )

    assert (
        manifest["geo_batch_version"]
        == "geo_batch_v1"
    )

    assert (
        manifest["platform_code"]
        == "qwen"
    )

    assert (
        manifest["platform_name"]
        == "千问"
    )

    assert (
        manifest["product_id"]
        == "hongmao"
    )

    assert (
        manifest["product_name"]
        == "鸿茅药酒"
    )

    assert (
        manifest["batch_id"]
        == "qwen-central-test"
    )

    task = json.loads(
        (
            package_dir
            / "tasks.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()[0]
    )

    assert task["mode_code"] == "expert"
    assert task["task_status"] == "success"
    assert task["task_id"]

    answer_record = json.loads(
        (
            package_dir
            / "answers.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()[0]
    )

    assert (
        answer_record["task_id"]
        == task["task_id"]
    )

    assert (
        answer_record["answer_text_raw"]
        == "研究回答"
    )

    assert (
        answer_record["mode_code"]
        == "expert"
    )

    assert (
        answer_record[
            "platform_meta_json"
        ]["original_mode"]
        == "research"
    )

    source = json.loads(
        (
            package_dir
            / "sources.jsonl"
        ).read_text(
            encoding="utf-8"
        ).splitlines()[0]
    )

    assert (
        source["answer_id"]
        == answer_record["answer_id"]
    )

    assert (
        source["source_order"]
        == 1
    )

    assert (
        source["source_url_raw"]
        == "https://example.com/1"
    )


def test_central_directory_exports_only_referenced_screenshots(
    tmp_path: Path, central_batch_factory,
) -> None:
    batch_dir = central_batch_factory()
    ref = "screenshots/Q001_quick.png"
    (batch_dir / "screenshots/orphan.png").write_bytes(b"unreferenced")
    (batch_dir / "unrelated.txt").write_text("unrelated", encoding="utf-8")
    package_dir = export_central_package_directory(
        batch_dir=batch_dir,
        output_dir=tmp_path / "package",
        batch_id="central-test",
        product_id="product",
        product_name="测试产品",
    )
    manifest = json.loads((package_dir / "manifest.json").read_text("utf-8"))
    answers = [json.loads(line) for line in
               (package_dir / "answers.jsonl").read_text("utf-8").splitlines()]
    checksums = json.loads((package_dir / "checksums.json").read_text("utf-8"))

    assert manifest["capabilities"]["supports_screenshot"] is True
    assert manifest["files"] == PACKAGE_FILES
    assert answers[0]["screenshot_path"] == ref
    assert (package_dir / ref).read_bytes() == (batch_dir / ref).read_bytes()
    assert set(checksums) == {*CHECKSUM_TARGET_FILES, ref}
    assert checksums[ref] == hashlib.sha256((package_dir / ref).read_bytes()).hexdigest()
    assert {path.relative_to(package_dir).as_posix()
            for path in package_dir.rglob("*") if path.is_file()} == {*PACKAGE_FILES, ref}


@pytest.mark.parametrize("refs", [(), (None,), ("",)])
def test_central_directory_without_screenshots(
    tmp_path: Path, central_batch_factory, refs,
) -> None:
    package_dir = export_central_package_directory(
        batch_dir=central_batch_factory(refs),
        output_dir=tmp_path / "package",
        batch_id="central-test",
        product_id="product",
        product_name="测试产品",
    )
    manifest = json.loads((package_dir / "manifest.json").read_text("utf-8"))
    checksums = json.loads((package_dir / "checksums.json").read_text("utf-8"))
    assert manifest["capabilities"]["supports_screenshot"] is False
    assert not (package_dir / "screenshots").exists()
    assert set(checksums) == set(CHECKSUM_TARGET_FILES)


@pytest.mark.parametrize(
    ("refs", "reason"),
    [
        (("screenshots/Q001_quick.png", None), "partial screenshot coverage"),
        (("screenshots/Q001_quick.png", "screenshots/Q001_quick.png"),
         "duplicate screenshot reference"),
        (("../evil.png",), "invalid central screenshot reference"),
    ],
)
def test_central_directory_rejects_invalid_screenshot_coverage(
    tmp_path: Path, central_batch_factory, refs, reason: str,
) -> None:
    with pytest.raises(ValueError, match=reason):
        export_central_package_directory(
            batch_dir=central_batch_factory(refs),
            output_dir=tmp_path / "package",
            batch_id="central-test",
            product_id="product",
            product_name="测试产品",
        )


@pytest.mark.parametrize("is_directory", [False, True])
def test_central_directory_rejects_missing_or_nonfile_screenshot(
    tmp_path: Path, central_batch_factory, is_directory: bool,
) -> None:
    batch_dir = central_batch_factory()
    screenshot = batch_dir / "screenshots/Q001_quick.png"
    screenshot.unlink()
    if is_directory:
        screenshot.mkdir()
    with pytest.raises(ValueError if is_directory else FileNotFoundError):
        export_central_package_directory(
            batch_dir=batch_dir,
            output_dir=tmp_path / "package",
            batch_id="central-test",
            product_id="product",
            product_name="测试产品",
        )


@pytest.mark.parametrize("ref", [
    None, 123, "", "../a.png", "screenshots/../a.png", r"C:\a.png",
    "/screenshots/a.png", "screenshots/a/b.png", "screenshots/./a.png",
    r"screenshots\a.png", "screenshots/..", "screenshots/.", "screenshots/",
    "screenshots/.png", "screenshots/a.jpg", "screenshots/a.PNG",
    "other/a.png", "screenshots/C:a.png", "screenshots/a\x00.png",
])
def test_central_screenshot_ref_rejects_unsafe_paths(ref) -> None:
    with pytest.raises(ValueError):
        validate_central_screenshot_ref(ref)


@pytest.mark.parametrize("ref", [
    "screenshots/Q001_quick.png", "screenshots/Q001_research.png",
])
def test_central_screenshot_ref_accepts_png_filename(ref: str) -> None:
    assert validate_central_screenshot_ref(ref) == ref
