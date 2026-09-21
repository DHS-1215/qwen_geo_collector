from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from app.qwen.exceptions import (
    QwenQuotaExhaustedError,
    QwenRiskControlError,
    QwenRefusalError,
    QwenServiceBusyError,
)
from app.qwen.models import (
    QwenAnswerResult,
    QwenBatchSummary,
    QwenTaskRunResult,
)
from app.qwen.runner import (
    QwenRunner,
)
from app.qwen.serialization import (
    write_result_json,
)
from app.qwen.tasks import (
    QwenTask,
)
from app.qwen.refusal import (
    is_qwen_refusal,
)
from app.qwen.quota import (
    is_qwen_quota_exhausted,
)
from app.qwen.service_busy import (
    is_qwen_service_busy,
)

QUICK_TASK_GAP_MS = 5000
RESEARCH_TASK_GAP_MS = 12000
REFUSAL_RETRY_WAIT_SECONDS = 600
REFUSAL_MAX_RETRIES = 1
SERVICE_BUSY_RETRY_WAIT_SECONDS = 60
SERVICE_BUSY_MAX_RETRIES = 1


class QwenBatchRunner:
    def __init__(
            self,
            runner: QwenRunner,
            output_dir: str | Path,
    ) -> None:
        self.runner = runner
        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _get_task_gap_ms(
            self,
            task: QwenTask,
    ) -> int:
        if task.mode == "research":
            return RESEARCH_TASK_GAP_MS

        return QUICK_TASK_GAP_MS

    def _build_output_path(
            self,
            task: QwenTask,
    ) -> Path:
        filename = (
            f"{task.question_id}_"
            f"{task.mode}.json"
        )

        return (
                self.output_dir
                / filename
        )

    def _write_task_issue(
            self,
            task: QwenTask,
            exc: Exception,
            *,
            status: str,
    ) -> Path:
        if status == "blocked":
            suffix = "blocked"
        else:
            suffix = "failed"

        path = (
                self.output_dir
                / (
                    f"{task.question_id}_"
                    f"{task.mode}_"
                    f"{suffix}.json"
                )
        )

        data = {
            "question_id": task.question_id,
            "question": task.question,
            "mode": task.mode,
            "status": status,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }

        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return path

    def _cleanup_task_issue_files(
            self,
            task: QwenTask,
    ) -> None:
        candidates = [
            (
                    self.output_dir
                    / (
                        f"{task.question_id}_"
                        f"{task.mode}_failed.json"
                    )
            ),
            (
                    self.output_dir
                    / (
                        f"{task.question_id}_"
                        f"{task.mode}_blocked.json"
                    )
            ),
        ]

        for path in candidates:
            if path.exists():
                path.unlink()

                print(
                    "[CLEANUP]",
                    path.name,
                )

    def _write_batch_summary(
            self,
            summary: QwenBatchSummary,
    ) -> Path:
        path = (
                self.output_dir
                / "batch_summary.json"
        )

        data = summary.model_dump(
            mode="json"
        )

        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return path

    def _load_passed_task_keys(
            self,
    ) -> set[tuple[str, str]]:
        summary_path = (
                self.output_dir
                / "batch_summary.json"
        )

        if not summary_path.exists():
            return set()

        try:
            data = json.loads(
                summary_path.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:
            return set()

        passed: set[
            tuple[str, str]
        ] = set()

        for item in data.get(
                "task_results",
                []
        ):
            if item.get(
                    "status"
            ) != "pass":
                continue

            question_id = item.get(
                "question_id"
            )

            mode = item.get(
                "mode"
            )

            if (
                    question_id
                    and mode
            ):
                passed.add(
                    (
                        question_id,
                        mode,
                    )
                )

        return passed

    def _ask_with_refusal_retry(
            self,
            task: QwenTask,
            *,
            timeout_seconds: int,
    ) -> QwenAnswerResult:

        def ask_once() -> QwenAnswerResult:
            return self.runner.ask(
                task.question,
                mode=task.mode,
                new_chat=True,
                answer_timeout_seconds=(
                    timeout_seconds
                ),
            )

        def check_quota(
                result: QwenAnswerResult,
        ) -> None:
            if not is_qwen_quota_exhausted(
                    result.answer
            ):
                return

            print()
            print(
                "[QUOTA EXHAUSTED]",
                task.question_id,
                task.mode,
            )

            raise QwenQuotaExhaustedError(
                "Qwen account quota exhausted: "
                f"{task.question_id} "
                f"{task.mode}"
            )

        def recover_service_busy(
                result: QwenAnswerResult,
        ) -> QwenAnswerResult:
            check_quota(result)

            if not is_qwen_service_busy(
                    result.answer
            ):
                return result

            print()
            print(
                "[SERVICE BUSY DETECTED]",
                task.question_id,
                task.mode,
            )

            for retry_index in range(
                    SERVICE_BUSY_MAX_RETRIES
            ):
                print(
                    "[SERVICE BUSY WAIT]",
                    SERVICE_BUSY_RETRY_WAIT_SECONDS,
                    "seconds",
                )

                time.sleep(
                    SERVICE_BUSY_RETRY_WAIT_SECONDS
                )

                print(
                    "[SERVICE BUSY RETRY]",
                    retry_index + 1,
                    "/",
                    SERVICE_BUSY_MAX_RETRIES,
                )

                candidate = ask_once()

                check_quota(candidate)

                if not is_qwen_service_busy(
                        candidate.answer
                ):
                    print(
                        "[SERVICE BUSY RECOVERED]",
                        task.question_id,
                        task.mode,
                    )

                    return candidate

            raise QwenServiceBusyError(
                "Qwen service busy persisted after "
                f"{SERVICE_BUSY_MAX_RETRIES} retry: "
                f"{task.question_id} "
                f"{task.mode}"
            )

        result = recover_service_busy(
            ask_once()
        )

        if not is_qwen_refusal(
                result.answer
        ):
            return result

        print()
        print(
            "[REFUSAL DETECTED]",
            task.question_id,
            task.mode,
        )

        for retry_index in range(
                REFUSAL_MAX_RETRIES
        ):
            print(
                "[REFUSAL WAIT]",
                REFUSAL_RETRY_WAIT_SECONDS,
                "seconds",
            )

            time.sleep(
                REFUSAL_RETRY_WAIT_SECONDS
            )

            print(
                "[REFUSAL RETRY]",
                retry_index + 1,
                "/",
                REFUSAL_MAX_RETRIES,
            )

            result = recover_service_busy(
                ask_once()
            )

            if not is_qwen_refusal(
                    result.answer
            ):
                print(
                    "[REFUSAL RECOVERED]",
                    task.question_id,
                    task.mode,
                )

                return result

        raise QwenRefusalError(
            "Qwen refusal persisted after "
            f"{REFUSAL_MAX_RETRIES} retry: "
            f"{task.question_id} "
            f"{task.mode}"
        )

    def run_task(
            self,
            task: QwenTask,
    ) -> QwenAnswerResult:
        print()

        print(
            "[TASK START]",
            task.question_id,
            task.mode,
        )

        print(
            "[QUESTION]",
            task.question,
        )

        timeout_seconds = (
            240
            if task.mode == "research"
            else 90
        )

        result = (
            self._ask_with_refusal_retry(
                task,
                timeout_seconds=(
                    timeout_seconds
                ),
            )
        )

        # Runner 只负责网页采集，
        # question_id 由 Batch 层补充。
        result.question_id = (
            task.question_id
        )

        output_path = (
            self._build_output_path(
                task
            )
        )

        write_result_json(
            result,
            output_path,
        )

        self._cleanup_task_issue_files(
            task
        )

        print(
            "[TASK PASS]",
            task.question_id,
            task.mode,
        )

        print(
            "[ANSWER LENGTH]",
            len(result.answer),
        )

        print(
            "[SEARCH QUERIES]",
            len(
                result.search_queries
            ),
        )

        print(
            "[SOURCES]",
            len(
                result.sources
            ),
        )

        print(
            "[OUTPUT]",
            output_path,
        )

        return result

    def run(
            self,
            tasks: list[QwenTask],
            *,
            resume: bool = False,
    ) -> list[QwenTaskRunResult]:
        task_results: list[
            QwenTaskRunResult
        ] = []

        total = len(tasks)
        started_at = datetime.now()

        existing_results: list[
            QwenTaskRunResult
        ] = []

        passed_task_keys: set[
            tuple[str, str]
        ] = set()

        if resume:
            existing_results = (
                self._load_existing_task_results()
            )

            passed_task_keys = (
                self._load_passed_task_keys()
            )

            print(
                "[RESUME] enabled"
            )

            print(
                "[RESUME] existing results:",
                len(existing_results),
            )

            print(
                "[RESUME] passed tasks:",
                len(passed_task_keys),
            )

        print(
            "[BATCH START]"
        )

        print(
            "[TASK COUNT]",
            total,
        )

        batch_paused = False

        for index, task in enumerate(
                tasks,
                start=1,
        ):
            print()

            print(
                f"[PROGRESS] "
                f"{index}/{total}"
            )

            task_key = (
                task.question_id,
                task.mode,
            )

            if (
                    resume
                    and task_key
                    in passed_task_keys
            ):
                print()

                print(
                    "[TASK SKIP]",
                    task.question_id,
                    task.mode,
                )

                print(
                    "[REASON] already passed"
                )

                continue

            # =====================================
            # 正常执行
            # =====================================

            try:
                self.run_task(
                    task
                )

                output_path = (
                    self._build_output_path(
                        task
                    )
                )

                task_results.append(
                    QwenTaskRunResult(
                        question_id=(
                            task.question_id
                        ),
                        mode=task.mode,
                        question=task.question,
                        status="pass",
                        output_path=str(
                            output_path
                        ),
                    )
                )

            # =====================================
            # 风控：立即暂停整个批次
            # =====================================

            except (

                    QwenRiskControlError,

                    QwenRefusalError,

                    QwenQuotaExhaustedError,

            ) as exc:
                print()

                print(
                    "[TASK BLOCKED]",
                    task.question_id,
                    task.mode,
                )

                print(
                    "[ERROR TYPE]",
                    type(exc).__name__,
                )

                print(
                    "[ERROR]",
                    str(exc),
                )

                if isinstance(
                        exc,
                        QwenQuotaExhaustedError,
                ):
                    print()
                    print(
                        "[ACCOUNT SWITCH REQUIRED]"
                    )
                    print(
                        "??????????????????"
                    )
                    print(
                        "???????????????????"
                    )
                    print(
                        "??????? --resume ???????"
                    )
                    print(
                        "???????? PASS?"
                        "?????????????"
                    )

                blocked_path = (
                    self._write_task_issue(
                        task,
                        exc,
                        status="blocked",
                    )
                )

                task_results.append(
                    QwenTaskRunResult(
                        question_id=(
                            task.question_id
                        ),
                        mode=task.mode,
                        question=task.question,
                        status="blocked",
                        output_path=str(
                            blocked_path
                        ),
                        error_type=(
                            type(exc).__name__
                        ),
                        error_message=str(
                            exc
                        ),
                    )
                )

                print(
                    "[BLOCKED OUTPUT]",
                    blocked_path,
                )

                print()

                print(
                    "[BATCH PAUSED]"
                )

                if isinstance(
                        exc,
                        QwenQuotaExhaustedError,
                ):
                    reason = (
                        "account quota exhausted"
                    )
                elif isinstance(
                        exc,
                        QwenRefusalError,
                ):
                    reason = (
                        "persistent refusal detected"
                    )
                else:
                    reason = (
                        "risk control detected"
                    )

                print(
                    "[REASON]",
                    reason,
                )

                batch_paused = True

                break

            # =====================================
            # 普通失败：记录后继续
            # =====================================

            except Exception as exc:
                print()

                print(
                    "[TASK FAIL]",
                    task.question_id,
                    task.mode,
                )

                print(
                    "[ERROR TYPE]",
                    type(exc).__name__,
                )

                print(
                    "[ERROR]",
                    str(exc),
                )

                failure_path = (
                    self._write_task_issue(
                        task,
                        exc,
                        status="fail",
                    )
                )

                task_results.append(
                    QwenTaskRunResult(
                        question_id=(
                            task.question_id
                        ),
                        mode=task.mode,
                        question=task.question,
                        status="fail",
                        output_path=str(
                            failure_path
                        ),
                        error_type=(
                            type(exc).__name__
                        ),
                        error_message=str(
                            exc
                        ),
                    )
                )

                print(
                    "[FAILURE OUTPUT]",
                    failure_path,
                )

            # =====================================
            # 最后一题之后不再等待
            # =====================================

            if index >= total:
                continue

            gap_ms = (
                self._get_task_gap_ms(
                    task
                )
            )

            print(
                "[TASK GAP MS]",
                gap_ms,
            )

            self.runner.page.wait_for_timeout(
                gap_ms
            )

        merged_results: dict[
            tuple[str, str],
            QwenTaskRunResult,
        ] = {}

        if resume:
            for item in existing_results:
                merged_results[
                    (
                        item.question_id,
                        item.mode,
                    )
                ] = item

        for item in task_results:
            merged_results[
                (
                    item.question_id,
                    item.mode,
                )
            ] = item

        all_task_results = list(
            merged_results.values()
        )

        # =========================================
        # 批次统计
        # =========================================

        pass_count = sum(
            item.status == "pass"
            for item in all_task_results
        )

        fail_count = sum(
            item.status == "fail"
            for item in all_task_results
        )

        blocked_count = sum(
            item.status == "blocked"
            for item in all_task_results
        )

        executed_count = len(
            all_task_results
        )

        pending_count = (
                total
                - executed_count
        )

        # =========================================
        # 判断整个批次状态
        # =========================================

        if blocked_count > 0:
            batch_status = "blocked"

        elif fail_count > 0:
            batch_status = "partial"

        else:
            batch_status = "completed"

        # =========================================
        # 写批次汇总
        # =========================================

        summary = QwenBatchSummary(
            status=batch_status,
            planned_count=total,
            executed_count=executed_count,
            pass_count=pass_count,
            fail_count=fail_count,
            blocked_count=blocked_count,
            pending_count=pending_count,
            task_results=all_task_results,
            started_at=started_at,
            finished_at=datetime.now(),
        )

        summary_path = (
            self._write_batch_summary(
                summary
            )
        )

        # =========================================
        # 最终日志
        # =========================================

        print()

        print(
            "[BATCH COMPLETE]"
        )

        print(
            "[BATCH STATUS]",
            batch_status,
        )

        print(
            "[PASS COUNT]",
            pass_count,
        )

        print(
            "[FAIL COUNT]",
            fail_count,
        )

        print(
            "[BLOCKED COUNT]",
            blocked_count,
        )

        print(
            "[EXECUTED COUNT]",
            executed_count,
        )

        print(
            "[PLANNED COUNT]",
            total,
        )

        print(
            "[PENDING COUNT]",
            pending_count,
        )

        print(
            "[BATCH PAUSED]",
            batch_paused,
        )

        print(
            "[SUMMARY]",
            summary_path,
        )

        return all_task_results

    def _load_passed_task_keys(
            self,
    ) -> set[tuple[str, str]]:
        summary_path = (
                self.output_dir
                / "batch_summary.json"
        )

        if not summary_path.exists():
            return set()

        try:
            data = json.loads(
                summary_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            return set()

        passed: set[
            tuple[str, str]
        ] = set()

        for item in data.get(
                "task_results",
                []
        ):
            if item.get("status") != "pass":
                continue

            question_id = item.get(
                "question_id"
            )

            mode = item.get(
                "mode"
            )

            if question_id and mode:
                passed.add(
                    (
                        question_id,
                        mode,
                    )
                )

        return passed

    def _load_existing_task_results(
            self,
    ) -> list[QwenTaskRunResult]:
        summary_path = (
                self.output_dir
                / "batch_summary.json"
        )

        if not summary_path.exists():
            return []

        try:
            data = json.loads(
                summary_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            return []

        results: list[
            QwenTaskRunResult
        ] = []

        for item in data.get(
                "task_results",
                []
        ):
            try:
                results.append(
                    QwenTaskRunResult(
                        **item
                    )
                )
            except Exception:
                continue

        return results
