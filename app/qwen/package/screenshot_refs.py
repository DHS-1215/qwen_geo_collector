from __future__ import annotations


def validate_central_screenshot_ref(ref: object) -> str:
    """Accept only a relative screenshots/<filename>.png reference."""
    if not isinstance(ref, str):
        raise ValueError("central screenshot reference must be a string")

    parts = ref.split("/")
    if (
        len(parts) != 2
        or parts[0] != "screenshots"
        or parts[1] in {".", "..", ".png"}
        or not parts[1].endswith(".png")
        or "\\" in ref
        or ":" in ref
        or any(ord(char) < 32 for char in ref)
    ):
        raise ValueError(f"invalid central screenshot reference: {ref!r}")

    return ref
