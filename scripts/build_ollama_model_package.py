from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path


MODEL_ROOT = Path(r"D:\models")

MANIFEST = (
    MODEL_ROOT
    / "manifests"
    / "registry.ollama.ai"
    / "library"
    / "qwen2.5"
    / "7b"
)

DIST = Path(__file__).resolve().parents[1] / "dist"


def digest_to_blob(digest: str) -> Path:
    if not digest.startswith("sha256:"):
        raise ValueError(f"Unsupported digest: {digest}")

    return (
        MODEL_ROOT
        / "blobs"
        / digest.replace(":", "-", 1)
    )


def main() -> None:
    if not MANIFEST.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST}"
        )

    manifest_data = json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )

    digests: list[str] = []

    config = manifest_data.get("config")
    if config and config.get("digest"):
        digests.append(config["digest"])

    for layer in manifest_data.get("layers", []):
        digest = layer.get("digest")
        if digest:
            digests.append(digest)

    # 去重但保持顺序
    digests = list(dict.fromkeys(digests))

    blobs: list[Path] = []

    for digest in digests:
        blob = digest_to_blob(digest)

        if not blob.exists():
            raise FileNotFoundError(
                f"Blob not found: {blob}"
            )

        blobs.append(blob)

    total_bytes = sum(
        blob.stat().st_size
        for blob in blobs
    )

    DIST.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    zip_path = (
        DIST
        / f"qwen2.5_7b_ollama_model_{timestamp}.zip"
    )

    print(
        f"[MODEL] qwen2.5:7b"
    )
    print(
        f"[BLOBS] {len(blobs)}"
    )
    print(
        f"[TOTAL GB] {total_bytes / 1024 / 1024 / 1024:.2f}"
    )

    # 模型本身已经压缩/量化过，
    # 使用 ZIP_STORED 避免浪费大量时间再次压缩。
    with zipfile.ZipFile(
        zip_path,
        mode="w",
        compression=zipfile.ZIP_STORED,
        allowZip64=True,
    ) as zf:

        manifest_arc = (
            Path("models")
            / "manifests"
            / "registry.ollama.ai"
            / "library"
            / "qwen2.5"
            / "7b"
        )

        zf.write(
            MANIFEST,
            manifest_arc.as_posix(),
        )

        for blob in blobs:
            arcname = (
                Path("models")
                / "blobs"
                / blob.name
            )

            print(
                "[ADD]",
                blob.name,
                f"{blob.stat().st_size / 1024 / 1024:.2f} MB",
            )

            zf.write(
                blob,
                arcname.as_posix(),
            )

    print()
    print(
        "[OLLAMA MODEL PACKAGE]",
        zip_path,
    )
    print(
        "[PACKAGE GB]",
        round(
            zip_path.stat().st_size
            / 1024
            / 1024
            / 1024,
            2,
        ),
    )


if __name__ == "__main__":
    main()
