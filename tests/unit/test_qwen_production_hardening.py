from app.qwen.answer_cleaning import clean_qwen_answer_text
from app.qwen.package.site_utils import source_site_name_from_url
from app.qwen.service_busy import is_qwen_service_busy


def test_qwen_service_busy_real_message() -> None:
    text = (
        "\u5f53\u524d\u8bbf\u95ee\u4eba\u6570\u8fc7\u591a"
        "\U0001f62d"
        "\uff0c"
        "\u75af\u72c2\u52a0\u670d\u52a1\u5668\u4e2d"
        "\uff0c"
        "\u8bf7\u7a0d\u540e\u518d\u8bd5"
        "\u3002"
    )

    assert is_qwen_service_busy(text)


def test_qwen_service_busy_does_not_match_normal_answer() -> None:
    text = (
        "\u6b63\u5e38\u56de\u7b54\u4e2d\u8ba8\u8bba"
        "\u670d\u52a1\u5668\u8d1f\u8f7d\u8fc7\u9ad8"
        "\u7684\u95ee\u9898\u3002"
    )

    assert not is_qwen_service_busy(text)


def test_clean_quick_answer_removes_video_card_tail() -> None:
    text = (
        "Normal answer body.\n"
        "00:30\n"
        "Hongmao product video\n"
        "creator123"
    )

    assert clean_qwen_answer_text(
        text,
        mode="quick",
    ) == "Normal answer body."


def test_clean_quick_answer_keeps_normal_text() -> None:
    text = "Normal answer body.\nSecond paragraph."

    assert clean_qwen_answer_text(
        text,
        mode="quick",
    ) == text


def test_clean_expert_answer_does_not_apply_quick_cleanup() -> None:
    text = (
        "Expert answer.\n"
        "00:30\n"
        "Example title\n"
        "creator123"
    )

    assert clean_qwen_answer_text(
        text,
        mode="research",
    ) == text


def test_source_site_name_removes_www() -> None:
    assert (
        source_site_name_from_url(
            "https://www.nbd.com.cn/article/test"
        )
        == "nbd.com.cn"
    )


def test_source_site_name_keeps_subdomain() -> None:
    assert (
        source_site_name_from_url(
            "https://health.baidu.com/test"
        )
        == "health.baidu.com"
    )


def test_source_site_name_empty_url() -> None:
    assert source_site_name_from_url(None) is None
    assert source_site_name_from_url("") is None
