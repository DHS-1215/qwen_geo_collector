from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from app.qwen.models import QwenAnswerResult


@pytest.fixture
def central_batch_factory(tmp_path: Path):
    """Build a completed local batch without a browser."""
    def make_batch(screenshot_paths=("screenshots/Q001_quick.png",)):
        batch_dir = tmp_path / "batch"
        batch_dir.mkdir()
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lE"
            "QVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        tasks = []
        for index, ref in enumerate(screenshot_paths, start=1):
            question_id = f"Q{index:03d}"
            tasks.append({
                "question_id": question_id,
                "mode": "quick",
                "question": "测试问题",
                "status": "pass",
            })
            result = QwenAnswerResult(
                question_id=question_id,
                question="测试问题",
                answer="测试回答",
                mode="quick",
                turn_id=f"turn-{index}",
                chat_url="https://www.qianwen.com/chat/test",
                screenshot_path=ref,
            )
            if ref:
                screenshot_dir = batch_dir / "screenshots"
                screenshot_dir.mkdir(exist_ok=True)
                (screenshot_dir / f"{question_id}_quick.png").write_bytes(png)
                result.screenshot_sha256 = hashlib.sha256(png).hexdigest()
                result.screenshot_size_bytes = len(png)
                result.screenshot_width = 1
                result.screenshot_height = 1
            answer_data = result.model_dump(mode="json")
            if ref is None:
                answer_data = {
                    key: value for key, value in answer_data.items()
                    if not key.startswith("screenshot_")
                }
            (batch_dir / f"{question_id}_quick.json").write_text(
                json.dumps(answer_data, ensure_ascii=False), encoding="utf-8"
            )

        count = len(tasks)
        summary = {
            "platform": "qwen",
            "status": "completed",
            "planned_count": count,
            "executed_count": count,
            "pass_count": count,
            "fail_count": 0,
            "blocked_count": 0,
            "pending_count": 0,
            "task_results": tasks,
            "started_at": "2026-09-01T12:00:00",
            "finished_at": "2026-09-01T12:05:00",
        }
        (batch_dir / "batch_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False), encoding="utf-8"
        )
        return batch_dir

    return make_batch
