from __future__ import annotations


KNOWN_REFUSAL_ANSWERS = frozenset(
    {
        "你好，我无法回答这个问题，我们换一个话题聊聊吧。",
    }
)


def normalize_refusal_text(
    text: str,
) -> str:
    return text.strip()


def is_qwen_refusal(
    answer: str,
) -> bool:
    normalized = normalize_refusal_text(
        answer
    )

    if not normalized:
        return False

    return (
        normalized
        in KNOWN_REFUSAL_ANSWERS
    )
