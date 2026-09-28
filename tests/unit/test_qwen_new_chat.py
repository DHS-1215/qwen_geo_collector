from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

import app.qwen.runner as runner_module
from app.qwen.exceptions import (
    QwenElementNotFoundError,
    QwenRiskControlError,
    QwenTimeoutError,
)
from app.qwen.runner import QwenRunner
from app.qwen.selectors import (
    ANSWER_WRAP_SELECTOR,
    INPUT_SELECTOR,
    QUESTION_WRAP_SELECTOR,
    RISK_CONTROL_TEXTS,
)


def make_locator(elements: list[MagicMock]) -> MagicMock:
    locator = MagicMock()
    locator.count.return_value = len(elements)
    locator.nth.side_effect = elements.__getitem__
    return locator


def make_page(
    *,
    questions: int = 1,
    answers: int = 1,
    input_visibility: tuple[bool, ...] = (True,),
    new_visible: bool | None = True,
    legacy_visible: bool | None = None,
):
    state = {
        "questions": questions,
        "answers": answers,
        "input_visibility": input_visibility,
        "risk_text": "",
    }
    page = MagicMock()
    page.url = "https://www.qianwen.com/"
    body = MagicMock()
    body.inner_text.side_effect = lambda: state["risk_text"]
    new_button = MagicMock()
    legacy_button = MagicMock()

    def open_blank_chat(*args, **kwargs) -> None:
        state["questions"] = 0
        state["answers"] = 0
        state["input_visibility"] = (True,)

    for button in (new_button, legacy_button):
        button.click.side_effect = open_blank_chat
        button.evaluate.side_effect = open_blank_chat

    def locate(selector: str) -> MagicMock:
        if selector == "body":
            return body
        if selector == INPUT_SELECTOR:
            inputs = []
            for visible in state["input_visibility"]:
                element = MagicMock()
                element.is_visible.return_value = visible
                inputs.append(element)
            return make_locator(inputs)
        if selector == QUESTION_WRAP_SELECTOR:
            return make_locator([MagicMock() for _ in range(state["questions"])])
        if selector == ANSWER_WRAP_SELECTOR:
            return make_locator([MagicMock() for _ in range(state["answers"])])
        raise AssertionError(f"unexpected selector: {selector}")

    def by_text(text: str, *, exact: bool) -> MagicMock:
        assert exact is True
        if text == "新对话":
            button, visible = new_button, new_visible
        elif text == "新建对话":
            button, visible = legacy_button, legacy_visible
        else:
            raise AssertionError(f"unexpected text: {text}")
        if visible is None:
            return make_locator([])
        button.is_visible.return_value = visible
        return make_locator([button])

    page.locator.side_effect = locate
    page.get_by_text.side_effect = by_text
    return page, state, new_button, legacy_button


@pytest.mark.parametrize("input_visibility", [(True,), (False, True)])
def test_new_chat_returns_when_blank_session_is_already_ready(
    input_visibility: tuple[bool, ...], capsys,
) -> None:
    page, _, new_button, legacy_button = make_page(
        questions=0,
        answers=0,
        input_visibility=input_visibility,
        new_visible=None,
    )

    QwenRunner(page).new_chat()

    assert "[NEW CHAT] already ready" in capsys.readouterr().out
    page.get_by_text.assert_not_called()
    new_button.click.assert_not_called()
    legacy_button.click.assert_not_called()
    page.wait_for_timeout.assert_not_called()


def test_new_chat_prefers_new_entry_over_legacy_entry() -> None:
    page, state, new_button, legacy_button = make_page(legacy_visible=True)

    QwenRunner(page).new_chat()

    page.get_by_text.assert_called_once_with("新对话", exact=True)
    new_button.click.assert_called_once_with(timeout=3000)
    new_button.evaluate.assert_not_called()
    legacy_button.click.assert_not_called()
    assert state["questions"] == state["answers"] == 0


@pytest.mark.parametrize("new_visible", [None, False])
def test_new_chat_falls_back_to_visible_legacy_entry(new_visible) -> None:
    page, _, new_button, legacy_button = make_page(
        new_visible=new_visible, legacy_visible=True,
    )

    QwenRunner(page).new_chat()

    assert page.get_by_text.call_args_list == [
        call("新对话", exact=True), call("新建对话", exact=True),
    ]
    new_button.click.assert_not_called()
    legacy_button.click.assert_called_once_with(timeout=3000)


def test_new_chat_raises_when_both_entries_are_missing() -> None:
    page, _, _, _ = make_page(new_visible=None, legacy_visible=None)

    with pytest.raises(QwenElementNotFoundError) as exc:
        QwenRunner(page).new_chat()

    assert str(exc.value) == "没有找到“新对话”入口"


@pytest.mark.parametrize("input_visibility", [(), (False,)])
def test_new_chat_does_not_treat_unloaded_page_as_ready(input_visibility) -> None:
    page, _, _, _ = make_page(
        questions=0, answers=0,
        input_visibility=input_visibility,
        new_visible=None,
    )

    with pytest.raises(QwenElementNotFoundError):
        QwenRunner(page).new_chat()

    assert page.get_by_text.call_count == 2


@pytest.mark.parametrize(("questions", "answers"), [(1, 0), (0, 1)])
def test_new_chat_requires_both_question_and_answer_counts_to_be_zero(
    questions: int, answers: int,
) -> None:
    page, _, new_button, _ = make_page(questions=questions, answers=answers)

    QwenRunner(page).new_chat()

    new_button.click.assert_called_once_with(timeout=3000)


def test_new_chat_keeps_dom_click_fallback() -> None:
    page, _, new_button, _ = make_page()
    new_button.click.side_effect = RuntimeError("normal click blocked")

    QwenRunner(page).new_chat()

    new_button.evaluate.assert_called_once_with("el => el.click()")


def test_new_chat_waits_for_visible_input_after_click() -> None:
    page, state, new_button, _ = make_page()

    def clear_chat(*args, **kwargs) -> None:
        state["questions"] = state["answers"] = 0
        state["input_visibility"] = (False,)

    def finish_loading(milliseconds: int) -> None:
        if milliseconds == 200:
            state["input_visibility"] = (True,)

    new_button.click.side_effect = clear_chat
    page.wait_for_timeout.side_effect = finish_loading

    QwenRunner(page).new_chat()

    assert page.wait_for_timeout.call_args_list == [call(500), call(200)]


def test_new_chat_times_out_when_input_stays_hidden_after_click(monkeypatch) -> None:
    page, state, new_button, _ = make_page()

    def clear_chat(*args, **kwargs) -> None:
        state["questions"] = state["answers"] = 0
        state["input_visibility"] = (False,)

    new_button.click.side_effect = clear_chat
    ticks = iter([0, 0, 11])
    monkeypatch.setattr(
        runner_module, "time", SimpleNamespace(monotonic=lambda: next(ticks)),
    )

    with pytest.raises(QwenTimeoutError):
        QwenRunner(page).new_chat(timeout_seconds=10)

    assert page.wait_for_timeout.call_args_list == [call(500), call(200)]


def test_new_chat_checks_risk_control_before_already_ready_return() -> None:
    page, state, _, _ = make_page(questions=0, answers=0)
    state["risk_text"] = RISK_CONTROL_TEXTS[0]

    with pytest.raises(QwenRiskControlError):
        QwenRunner(page).new_chat()

    page.get_by_text.assert_not_called()


def test_new_chat_checks_risk_control_after_click() -> None:
    page, state, new_button, _ = make_page()

    def show_risk_control(*args, **kwargs) -> None:
        state["risk_text"] = RISK_CONTROL_TEXTS[0]

    new_button.click.side_effect = show_risk_control

    with pytest.raises(QwenRiskControlError):
        QwenRunner(page).new_chat()
