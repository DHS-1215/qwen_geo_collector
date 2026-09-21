from __future__ import annotations

import re


_DURATION_RE = re.compile(
    r"^\d{1,2}:\d{2}$"
)

_CREATOR_RE = re.compile(
    r"^[A-Za-z0-9_\-\u4e00-\u9fff#?]{2,20}$"
)


def _looks_like_creator(
    text: str,
) -> bool:
    value = text.strip()

    return bool(
        _CREATOR_RE.fullmatch(value)
    ) and not bool(
        _DURATION_RE.fullmatch(value)
    )


def _looks_like_card_title(
    text: str,
) -> bool:
    value = text.strip()

    return (
        2 <= len(value) <= 120
        and not _DURATION_RE.fullmatch(value)
    )


def clean_qwen_answer_text(
    text: str | None,
    *,
    mode: str,
) -> str:
    value = (text or "").strip()

    if not value:
        return value

    if mode != "quick":
        return value

    lines = [
        line.rstrip()
        for line in value.splitlines()
    ]

    cut = len(lines)
    removed_cards = 0

    # Qwen Quick sometimes appends recommendation/video cards:
    #
    # 00:30
    # title
    # creator
    #
    # or:
    #
    # title
    # creator
    #
    # Parse backwards so the actual answer body is preserved.
    while cut >= 2:
        title = lines[cut - 2].strip()
        creator = lines[cut - 1].strip()

        if not (
            _looks_like_card_title(title)
            and _looks_like_creator(creator)
        ):
            break

        cut -= 2
        removed_cards += 1

        if (
            cut >= 1
            and _DURATION_RE.fullmatch(
                lines[cut - 1].strip()
            )
        ):
            cut -= 1

    if removed_cards == 0:
        return value

    return "\n".join(
        lines[:cut]
    ).rstrip()
