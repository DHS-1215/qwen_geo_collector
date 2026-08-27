from app.qwen.browser import QwenBrowserSession
from app.qwen.runner import QwenRunner


def main() -> None:
    session = QwenBrowserSession()

    try:
        page = session.connect()

        runner = QwenRunner(page)

        print(
            "[MODE] initial:",
            runner.get_mode(),
        )

        runner.set_mode("research")

        print(
            "[MODE] research:",
            runner.get_mode(),
        )

        runner.set_mode("quick")

        print(
            "[MODE] quick:",
            runner.get_mode(),
        )

        print(
            "[PASS] mode smoke completed"
        )

    finally:
        session.close()


if __name__ == "__main__":
    main()