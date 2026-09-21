from __future__ import annotations


MAX_SERVICE_BUSY_MESSAGE_LENGTH = 120

_SERVICE_BUSY_MARKERS = (
    "\u5f53\u524d\u8bbf\u95ee\u4eba\u6570\u8fc7\u591a",
    "\u75af\u72c2\u52a0\u670d\u52a1\u5668\u4e2d",
    "\u8bf7\u7a0d\u540e\u518d\u8bd5",
)


def is_qwen_service_busy(
    text: str | None,
) -> bool:
    if not text:
        return False

    value = " ".join(
        str(text).strip().split()
    )

    if len(value) > MAX_SERVICE_BUSY_MESSAGE_LENGTH:
        return False

    return all(
        marker in value
        for marker in _SERVICE_BUSY_MARKERS
    )
