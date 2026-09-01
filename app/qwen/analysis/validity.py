from __future__ import annotations

from app.qwen.models import (
    QwenAnswerResult,
    QwenTaskRunResult,
)
from app.qwen.refusal import (
    is_qwen_refusal,
)


def is_valid_analysis_answer(
    task_result: QwenTaskRunResult,
    answer_result: QwenAnswerResult | None,
) -> bool:
    if task_result.status != "pass":
        return False

    if answer_result is None:
        return False

    answer = answer_result.answer.strip()

    if not answer:
        return False

    if is_qwen_refusal(answer):
        return False

    return True