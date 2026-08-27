from app.qwen.browser import QwenBrowserSession
from app.qwen.runner import QwenRunner

QUESTION = (
    "鸿茅药酒到底是药还是酒？"
    "请基于公开网页资料回答，并附参考来源。"
)


def main() -> None:
    session = QwenBrowserSession()

    try:
        page = session.connect()

        runner = QwenRunner(page)

        result = runner.ask(
            QUESTION,
            mode="research",
            new_chat=True,
            answer_timeout_seconds=240,
        )

        print("[PASS] research completed")
        print("[MODE]", result.mode)
        print("[TURN]", result.turn_id)

        print()
        print("[ANSWER LENGTH]", len(result.answer))
        print("[ANSWER PREVIEW]")
        print(result.answer[:500])

        print()
        print("[SOURCE COUNT]", len(result.sources))

        for source in result.sources:
            print(
                f"[SOURCE {source.rank}] "
                f"{source.title}"
            )
            print(
                f"           {source.url}"
            )

        print()
        print(
            "[SEARCH QUERIES]",
            result.search_queries,
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()
