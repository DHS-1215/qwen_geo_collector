from __future__ import annotations

from typing import Literal

from app.qwen.models import QwenBatchSummary

PostBatchStatus = Literal[
    "completed",
    "partial",
    "blocked",
]


def resolve_post_batch_status(
        summary: QwenBatchSummary,
) -> PostBatchStatus:
    """
    根据批处理结果判断流水线下一步状态。

    completed:
        所有任务成功，可以继续导包。

    partial:
        存在普通失败，但没有 blocked / pending，
        可以继续导出部分成功包。

    blocked:
        存在风控阻塞或未执行任务，
        必须先 resume，不能生成最终包。
    """

    if (
            summary.blocked_count > 0
            or summary.pending_count > 0
    ):
        return "blocked"

    if summary.fail_count > 0:
        return "partial"

    return "completed"


def can_export_package(
        summary: QwenBatchSummary,
) -> bool:
    return (
            resolve_post_batch_status(summary)
            != "blocked"
    )
