from app.qwen.browser import (
    QwenBrowserSession,
)
from app.qwen.runner import (
    QwenRunner,
)
from app.qwen.selectors import (
    ANSWER_WRAP_SELECTOR,
)


def main() -> None:
    session = QwenBrowserSession()

    try:
        page = session.connect()

        runner = QwenRunner(
            page
        )

        answers = page.locator(
            ANSWER_WRAP_SELECTOR
        )

        if answers.count() == 0:
            raise RuntimeError(
                "当前页面没有回答"
            )

        answer_wrap = (
            answers.last
        )

        queries = (
            runner
            ._extract_search_queries(
                answer_wrap
            )
        )

        print()
        print(
            "[SEARCH QUERY COUNT]",
            len(queries),
        )

        for index, query in enumerate(
            queries,
            start=1,
        ):
            print(
                f"[QUERY {index}]",
                query,
            )

    finally:
        session.close()


if __name__ == "__main__":
    main()