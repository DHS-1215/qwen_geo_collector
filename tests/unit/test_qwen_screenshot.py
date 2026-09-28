from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path

import pytest

from app.qwen.screenshot import (
    capture_qwen_screenshot,
    validate_qwen_screenshot,
)


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunk(
    chunk_type: bytes,
    data: bytes,
) -> bytes:
    crc = zlib.crc32(
        chunk_type
    )

    crc = zlib.crc32(
        data,
        crc,
    ) & 0xFFFFFFFF

    return (
        struct.pack(
            ">I",
            len(data),
        )
        + chunk_type
        + data
        + struct.pack(
            ">I",
            crc,
        )
    )


def _make_png(
    width: int = 2,
    height: int = 3,
) -> bytes:
    ihdr = struct.pack(
        ">IIBBBBB",
        width,
        height,
        8,
        2,
        0,
        0,
        0,
    )

    scanline = (
        b"\x00"
        + (b"\x00\x00\x00" * width)
    )

    raw_image = (
        scanline * height
    )

    return (
        PNG_SIGNATURE
        + _png_chunk(
            b"IHDR",
            ihdr,
        )
        + _png_chunk(
            b"IDAT",
            zlib.compress(
                raw_image
            ),
        )
        + _png_chunk(
            b"IEND",
            b"",
        )
    )


class FakePage:
    def __init__(
        self,
        payload: bytes,
    ) -> None:
        self.payload = payload
        self.calls: list[
            tuple[str, bool]
        ] = []

    def screenshot(
        self,
        *,
        path: str,
        full_page: bool,
    ) -> bytes:
        self.calls.append(
            (
                path,
                full_page,
            )
        )

        Path(path).write_bytes(
            self.payload
        )

        return self.payload


def test_capture_qwen_screenshot_full_page_and_metadata(
    tmp_path: Path,
) -> None:
    payload = _make_png(
        width=1920,
        height=4320,
    )

    page = FakePage(
        payload
    )

    output_path = (
        tmp_path
        / "screenshots"
        / "Q001_quick.png"
    )

    evidence = (
        capture_qwen_screenshot(
            page,
            output_path,
        )
    )

    assert page.calls == [
        (
            str(output_path),
            True,
        )
    ]

    assert output_path.exists()

    assert evidence.path == output_path
    assert evidence.width == 1920
    assert evidence.height == 4320
    assert evidence.size_bytes == len(
        payload
    )
    assert evidence.sha256 == (
        hashlib.sha256(
            payload
        ).hexdigest()
    )


def test_validate_qwen_screenshot_rejects_invalid_signature(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "invalid.png"
    )

    path.write_bytes(
        b"not-a-png"
    )

    with pytest.raises(
        ValueError,
        match="signature",
    ):
        validate_qwen_screenshot(
            path
        )


def test_validate_qwen_screenshot_rejects_corrupt_crc(
    tmp_path: Path,
) -> None:
    payload = bytearray(
        _make_png()
    )

    payload[-1] ^= 0x01

    path = (
        tmp_path
        / "corrupt.png"
    )

    path.write_bytes(
        bytes(payload)
    )

    with pytest.raises(
        ValueError,
        match="CRC",
    ):
        validate_qwen_screenshot(
            path
        )


def test_validate_qwen_screenshot_rejects_zero_dimension(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "zero-width.png"
    )

    path.write_bytes(
        _make_png(
            width=0,
            height=1,
        )
    )

    with pytest.raises(
        ValueError,
        match="dimensions",
    ):
        validate_qwen_screenshot(
            path
        )