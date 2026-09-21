from app.qwen.quota import (
    is_qwen_quota_exhausted,
    normalize_quota_text,
)


def test_normalize_quota_text():
    assert (
        normalize_quota_text(
            "  今日使用次数\n已达上限  "
        )
        == "今日使用次数 已达上限"
    )


def test_detect_exact_quota_message():
    assert is_qwen_quota_exhausted(
        "今日使用次数已达上限"
    )


def test_detect_quota_message_with_extra_text():
    assert is_qwen_quota_exhausted(
        "抱歉，今日次数已用完，请稍后再试。"
    )


def test_empty_answer_is_not_quota():
    assert not is_qwen_quota_exhausted(
        ""
    )


def test_normal_answer_is_not_quota():
    assert not is_qwen_quota_exhausted(
        "鸿茅药酒属于药品，应按照药品说明书使用。"
    )


def test_long_normal_answer_with_quota_words_is_not_quota():
    answer = (
        "这是一段正常回答。"
        * 50
        + "文中可能讨论某个平台的额度不足问题。"
    )

    assert not is_qwen_quota_exhausted(
        answer
    )


def test_normal_answer_containing_quota_words_is_not_quota():
    assert not is_qwen_quota_exhausted(
        "正常回答：这个问题讨论的是额度不足的问题。"
    )
