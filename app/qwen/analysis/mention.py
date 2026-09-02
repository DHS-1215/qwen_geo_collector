from __future__ import annotations

import re
import unicodedata

from app.qwen.analysis.models import (
    MentionResult,
    MentionTarget,
)


WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_text(
    text: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFKC",
        text or "",
    )

    normalized = normalized.replace(
        "\u3000",
        " ",
    )

    normalized = normalized.lower()

    normalized = WHITESPACE_PATTERN.sub(
        " ",
        normalized,
    )

    return normalized.strip()


def _alias_pattern(
    alias: str,
) -> re.Pattern[str] | None:
    normalized_alias = normalize_text(
        alias
    )

    compact_alias = re.sub(
        r"\s+",
        "",
        normalized_alias,
    )

    if not compact_alias:
        return None

    pattern_text = r"\s*".join(
        re.escape(char)
        for char in compact_alias
    )

    return re.compile(
        pattern_text
    )


def analyze_target(
    answer: str,
    target: MentionTarget,
) -> MentionResult:
    normalized_answer = normalize_text(
        answer
    )

    mention_count = 0

    for alias in target.aliases:
        pattern = _alias_pattern(
            alias
        )

        if pattern is None:
            continue

        mention_count += len(
            pattern.findall(
                normalized_answer
            )
        )

    return MentionResult(
        target_id=target.target_id,
        mention_count=mention_count,
        mentioned=mention_count > 0,
    )
