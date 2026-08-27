from app.qwen.browser import (
    QwenBrowserSession,
)
from app.qwen.runner import (
    QwenRunner,
)

QUESTION = (
    "请只回答：QWEN_RUNNER_SMOKE_OK"
)


def main() -> None:
    session = QwenBrowserSession()

    try:
        page = session.connect()

        print(
            "[PASS] browser connected"
        )

        runner = QwenRunner(
            page
        )

        result = runner.ask(
            QUESTION,
            new_chat=True,
        )

        print()
        print("[PASS] ask completed")
        print(
            "[TURN]",
            result.turn_id,
        )
        print(
            "[QUESTION]",
            result.question,
        )
        print(
            "[ANSWER]",
            result.answer,
        )
        print(
            "[URL]",
            result.chat_url,
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()
