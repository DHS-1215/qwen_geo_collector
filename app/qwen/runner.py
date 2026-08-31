from __future__ import annotations

import json
import re
import time

from playwright.sync_api import (
    Locator,
    Page,
)

from app.qwen.exceptions import (
    QwenElementNotFoundError,
    QwenModeError,
    QwenRiskControlError,
    QwenTimeoutError,
)
from app.qwen.models import (
    QwenAnswerResult,
    QwenSource,
)
from app.qwen.selectors import (
    ANSWER_FEEDBACK_SELECTOR,
    ANSWER_FINAL_SELECTOR,
    ANSWER_WRAP_SELECTOR,
    INPUT_SELECTOR,
    MODE_MENU_BUTTON_SELECTOR,
    MODE_VALUES,
    QUESTION_TEXT_SELECTOR,
    QUESTION_WRAP_SELECTOR,
    RESEARCH_WORKFLOW_SELECTOR,
    RISK_CONTROL_TEXTS,
    SEND_BUTTON_SELECTOR,
    SOURCE_LINK_SELECTOR,
    QUICK_SOURCE_CARD_SELECTOR,
    QUICK_SOURCE_ENTRY_SELECTOR,
    QUICK_SOURCE_PANEL_SELECTOR,
)

NEW_CHAT_SETTLE_MS = 1500
MODE_SETTLE_MS = 1500
INPUT_SETTLE_MS = 1000
BEFORE_SEND_MS = 1000
ANSWER_SETTLE_MS = 1500
SOURCE_EXPAND_SETTLE_MS = 1500


class QwenRunner:
    def __init__(
            self,
            page: Page,
    ) -> None:
        self.page = page

    # =========================================
    # 公共页面状态
    # =========================================

    def detect_risk_control(self) -> bool:
        body_text = (
            self.page
            .locator("body")
            .inner_text()
        )

        return any(
            text in body_text
            for text in RISK_CONTROL_TEXTS
        )

    def ensure_no_risk_control(
            self,
    ) -> None:
        if self.detect_risk_control():
            raise QwenRiskControlError(
                "检测到千问真人验证 / 风控"
            )

    @staticmethod
    def _first_visible(
            locator: Locator,
    ) -> Locator | None:
        for index in range(
                locator.count()
        ):
            item = locator.nth(index)

            try:
                if item.is_visible():
                    return item
            except Exception:
                continue

        return None

    def _wait_for_send_button_enabled(
            self,
            timeout_seconds: int = 8,
    ) -> Locator:
        start = time.monotonic()

        while (
                time.monotonic() - start
                < timeout_seconds
        ):
            self.ensure_no_risk_control()

            send_button = self._first_visible(
                self.page.locator(
                    SEND_BUTTON_SELECTOR
                )
            )

            if send_button is not None:
                try:
                    disabled = (
                        send_button.is_disabled()
                    )

                    aria_disabled = (
                        send_button.get_attribute(
                            "aria-disabled"
                        )
                    )

                    if (
                            not disabled
                            and aria_disabled != "true"
                    ):
                        print(
                            "[SEND] button enabled"
                        )
                        return send_button

                except Exception:
                    pass

            self.page.wait_for_timeout(
                200
            )

        input_box = self._first_visible(
            self.page.locator(
                INPUT_SELECTOR
            )
        )

        input_text = ""

        if input_box is not None:
            try:
                input_text = (
                    input_box
                    .inner_text()
                    .strip()
                )
            except Exception:
                pass

        print(
            "[SEND] timeout, input text:",
            repr(input_text),
        )

        raise QwenTimeoutError(
            "填写问题后等待发送按钮激活超时"
        )

    # =========================================
    # 新建对话
    # =========================================

    def new_chat(
            self,
            timeout_seconds: int = 10,
    ) -> None:
        self.ensure_no_risk_control()

        old_url = self.page.url

        locator = self.page.get_by_text(
            "新建对话",
            exact=True,
        )

        button = self._first_visible(
            locator
        )

        if button is None:
            raise QwenElementNotFoundError(
                "没有找到“新建对话”按钮"
            )

        print(
            "[NEW CHAT] candidate found"
        )

        clicked = False

        # =========================================
        # 1. 优先正常点击
        # =========================================

        try:
            button.click(
                timeout=3000
            )

            print(
                "[NEW CHAT] normal click success"
            )

            clicked = True

        except Exception as exc:
            print(
                "[NEW CHAT] normal click blocked:",
                type(exc).__name__,
            )

        # =========================================
        # 2. 正常点击失败时走 DOM click
        # =========================================

        if not clicked:
            try:
                button.evaluate(
                    "el => el.click()"
                )

                print(
                    "[NEW CHAT] DOM click success"
                )

                clicked = True

            except Exception as exc:
                print(
                    "[NEW CHAT] DOM click failed:",
                    type(exc).__name__,
                )

        if not clicked:
            raise QwenElementNotFoundError(
                "无法点击“新建对话”"
            )

        # 给前端路由和 DOM 切换一点时间
        self.page.wait_for_timeout(
            500
        )

        # =========================================
        # 3. 等待真正进入空白新会话
        # =========================================

        start = time.monotonic()

        while (
                time.monotonic() - start
                < timeout_seconds
        ):
            self.ensure_no_risk_control()

            questions = (
                self.page.locator(
                    QUESTION_WRAP_SELECTOR
                ).count()
            )

            answers = (
                self.page.locator(
                    ANSWER_WRAP_SELECTOR
                ).count()
            )

            print(
                "[NEW CHAT] questions:",
                questions,
                "answers:",
                answers,
            )

            if (
                    questions == 0
                    and answers == 0
            ):
                print(
                    "[NEW CHAT] ready"
                )
                return

            self.page.wait_for_timeout(
                200
            )

        raise QwenTimeoutError(
            f"新建对话等待超时，"
            f"原 URL: {old_url}，"
            f"当前 URL: {self.page.url}"
        )

    # =========================================
    # Turn
    # =========================================

    def _get_turn_ids(
            self,
    ) -> set[str]:
        locator = self.page.locator(
            QUESTION_WRAP_SELECTOR
        )

        result: set[str] = set()

        for index in range(
                locator.count()
        ):
            value = (
                locator
                .nth(index)
                .get_attribute(
                    "data-chat-question-wrap"
                )
            )

            if value:
                result.add(value)

        return result

    def _wait_for_new_turn(
            self,
            previous_ids: set[str],
            timeout_seconds: int = 20,
    ) -> str:
        start = time.monotonic()

        while (
                time.monotonic() - start
                < timeout_seconds
        ):
            self.ensure_no_risk_control()

            current_ids = (
                self._get_turn_ids()
            )

            new_ids = (
                    current_ids -
                    previous_ids
            )

            if new_ids:
                return next(
                    iter(new_ids)
                )

            self.page.wait_for_timeout(
                200
            )

        raise QwenTimeoutError(
            "等待新问题 turn_id 超时"
        )

    # =========================================
    # 回答
    # =========================================

    def _wait_for_answer(
            self,
            turn_id: str,
            timeout_seconds: int = 60,
    ) -> str:
        answer_wrap = self.page.locator(
            f'[data-chat-answers-wrap="{turn_id}"]'
        )

        start = time.monotonic()

        while (
                time.monotonic() - start
                < timeout_seconds
        ):
            self.ensure_no_risk_control()

            if answer_wrap.count() > 0:
                final_answer = (
                    answer_wrap.locator(
                        ANSWER_FINAL_SELECTOR
                    )
                )

                feedback = (
                    answer_wrap.locator(
                        ANSWER_FEEDBACK_SELECTOR
                    )
                )

                if (
                        final_answer.count() > 0
                        and feedback.count() > 0
                ):
                    answer = (
                        final_answer
                        .last
                        .inner_text()
                        .strip()
                    )

                    if answer:
                        return answer

            self.page.wait_for_timeout(
                300
            )

        raise QwenTimeoutError(
            f"等待回答完成超时: {turn_id}"
        )

    # =========================================
    # Quick 来源
    # =========================================

    def _get_quick_source_req_id(
            self,
            answer_wrap: Locator,
    ) -> str | None:
        entries = answer_wrap.locator(
            QUICK_SOURCE_ENTRY_SELECTOR
        )

        print(
            "[QUICK SOURCE] entry count:",
            entries.count(),
        )

        if entries.count() == 0:
            return None

        entry = entries.first

        entry_id = (
                entry.get_attribute("id")
                or ""
        ).strip()

        prefix = "reference-link-anchor-"

        if not entry_id.startswith(prefix):
            return None

        req_id = entry_id[
                 len(prefix):
                 ].strip()

        return req_id or None

    def _get_quick_source_cards(
            self,
            req_id: str,
    ) -> list[Locator]:
        panel = self.page.locator(
            QUICK_SOURCE_PANEL_SELECTOR
        )

        if panel.count() == 0:
            return []

        cards = panel.locator(
            QUICK_SOURCE_CARD_SELECTOR
        )

        matched: list[Locator] = []

        for index in range(
                cards.count()
        ):
            card = cards.nth(index)

            raw = card.get_attribute(
                "data-click-extra"
            )

            if not raw:
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if (
                    str(
                        data.get("req_id")
                        or ""
                    )
                    == req_id
            ):
                matched.append(card)

        return matched

    def _open_quick_sources(
            self,
            answer_wrap: Locator,
            req_id: str,
            timeout_seconds: int = 5,
    ) -> list[Locator]:
        # 如果当前右侧已经是这一条回答的来源，
        # 不要再次点击，否则会把面板关闭。
        cards = (
            self._get_quick_source_cards(
                req_id
            )
        )

        if cards:
            print(
                "[QUICK SOURCE] "
                "panel already open"
            )
            return cards

        source_texts = answer_wrap.get_by_text(
            re.compile(
                r"^\s*\d+\s*[篇条]来源\s*$"
            )
        )

        print(
            "[QUICK SOURCE] "
            "source text count:",
            source_texts.count(),
        )

        if source_texts.count() == 0:
            return []

        source_text = (
            source_texts.first
        )

        try:
            source_text.click(
                timeout=3000
            )

            print(
                "[QUICK SOURCE] "
                "open click success"
            )

        except Exception as exc:
            print(
                "[QUICK SOURCE] "
                "normal click failed:",
                type(exc).__name__,
            )

            try:
                source_text.evaluate(
                    "el => el.click()"
                )

                print(
                    "[QUICK SOURCE] "
                    "DOM click success"
                )

            except Exception as dom_exc:
                print(
                    "[QUICK SOURCE] "
                    "DOM click failed:",
                    type(dom_exc).__name__,
                )
                return []

        start = time.monotonic()

        while (
                time.monotonic() - start
                < timeout_seconds
        ):
            cards = (
                self._get_quick_source_cards(
                    req_id
                )
            )

            if cards:
                print(
                    "[QUICK SOURCE] cards ready:",
                    len(cards),
                )
                return cards

            self.page.wait_for_timeout(
                200
            )

        print(
            "[QUICK SOURCE] "
            "source cards timeout"
        )

        return []

    def _extract_quick_sources(
            self,
            answer_wrap: Locator,
    ) -> list[QwenSource]:
        req_id = (
            self._get_quick_source_req_id(
                answer_wrap
            )
        )

        print(
            "[QUICK SOURCE] req_id:",
            req_id,
        )

        if not req_id:
            print(
                "[QUICK SOURCE] "
                "no source entry"
            )
            return []

        cards = self._open_quick_sources(
            answer_wrap,
            req_id,
        )

        print(
            "[QUICK SOURCE] raw cards:",
            len(cards),
        )

        sources: list[QwenSource] = []
        seen_urls: set[str] = set()

        for index, card in enumerate(
                cards
        ):
            raw = card.get_attribute(
                "data-click-extra"
            )

            if not raw:
                continue

            try:
                data = json.loads(raw)

            except json.JSONDecodeError:
                print(
                    f"[QUICK SOURCE] "
                    f"card {index} invalid JSON"
                )
                continue

            title = str(
                data.get("title")
                or ""
            ).strip()

            url = str(
                data.get("ref_url")
                or data.get("url")
                or ""
            ).strip()

            rank_raw = str(
                data.get("refer_num")
                or ""
            ).strip()

            if not title or not url:
                continue

            if url in seen_urls:
                continue

            try:
                rank = int(rank_raw)
            except ValueError:
                rank = len(sources) + 1

            seen_urls.add(url)

            source = QwenSource(
                rank=rank,
                title=title,
                url=url,
            )

            sources.append(source)

            print(
                f"[QUICK SOURCE {source.rank}] "
                f"{source.title}"
            )
            print(
                f"                 "
                f"{source.url}"
            )

        sources.sort(
            key=lambda item: item.rank
        )

        print(
            "[QUICK SOURCE] extracted:",
            len(sources),
        )

        return sources

    # =========================================
    # Research 来源
    # =========================================

    def _expand_research_sources(
            self,
            answer_wrap: Locator,
    ) -> None:
        workflow = answer_wrap.locator(
            RESEARCH_WORKFLOW_SELECTOR
        )

        print(
            "[SOURCE] workflow count:",
            workflow.count(),
        )

        if workflow.count() == 0:
            print(
                "[SOURCE] no research workflow"
            )
            return

        source_links = workflow.locator(
            SOURCE_LINK_SELECTOR
        )

        before_count = (
            source_links.count()
        )

        print(
            "[SOURCE] links before expand:",
            before_count,
        )

        view_all_candidates = (
            workflow.get_by_text(
                "查看全部",
                exact=True,
            )
        )

        candidate_count = (
            view_all_candidates.count()
        )

        print(
            "[SOURCE] 查看全部 candidates:",
            candidate_count,
        )

        if candidate_count == 0:
            print(
                "[SOURCE] no 查看全部 button"
            )
            return

        for index in range(
                candidate_count
        ):
            candidate = (
                view_all_candidates
                .nth(index)
            )

            try:
                visible = (
                    candidate.is_visible()
                )
            except Exception:
                visible = False

            print(
                f"[SOURCE] candidate {index} "
                f"visible:",
                visible,
            )

            if not visible:
                continue

            clicked = False

            try:
                candidate.click(
                    timeout=3000
                )

                print(
                    f"[SOURCE] candidate {index} "
                    f"normal click success"
                )

                clicked = True

            except Exception as exc:
                print(
                    f"[SOURCE] candidate {index} "
                    f"normal click blocked:",
                    type(exc).__name__,
                )

                try:
                    candidate.evaluate(
                        "el => el.click()"
                    )

                    print(
                        f"[SOURCE] candidate {index} "
                        f"DOM click success"
                    )

                    clicked = True

                except Exception as dom_exc:
                    print(
                        f"[SOURCE] candidate {index} "
                        f"DOM click failed:",
                        type(dom_exc).__name__,
                    )

            if not clicked:
                continue

            self.page.wait_for_timeout(
                SOURCE_EXPAND_SETTLE_MS
            )

            after_count = (
                workflow.locator(
                    SOURCE_LINK_SELECTOR
                ).count()
            )

            print(
                "[SOURCE] links after expand:",
                after_count,
            )

            if after_count > before_count:
                print(
                    "[SOURCE] source expansion success"
                )
                return

            if (
                    before_count > 0
                    and after_count == before_count
            ):
                print(
                    "[SOURCE] link count unchanged"
                )

        print(
            "[SOURCE] warning: "
            "source list was not expanded"
        )

    def _extract_sources(
            self,
            answer_wrap: Locator,
    ) -> list[QwenSource]:
        workflow = answer_wrap.locator(
            RESEARCH_WORKFLOW_SELECTOR
        )

        print(
            "[SOURCE] extract workflow count:",
            workflow.count(),
        )

        if workflow.count() == 0:
            return []

        links = workflow.locator(
            SOURCE_LINK_SELECTOR
        )

        raw_count = links.count()

        print(
            "[SOURCE] raw links:",
            raw_count,
        )

        sources: list[QwenSource] = []

        seen_urls: set[str] = set()

        for index in range(
                raw_count
        ):
            link = links.nth(index)

            try:
                href = link.get_attribute(
                    "href"
                )

                title = (
                    link.inner_text()
                    .strip()
                )

            except Exception as exc:
                print(
                    f"[SOURCE] link {index} "
                    f"read failed:",
                    type(exc).__name__,
                )
                continue

            if not href:
                continue

            href = href.strip()

            if not href:
                continue

            if href in seen_urls:
                continue

            if not title:
                continue

            seen_urls.add(
                href
            )

            source = QwenSource(
                rank=len(sources) + 1,
                title=title,
                url=href,
            )

            sources.append(
                source
            )

            print(
                f"[SOURCE {source.rank}] "
                f"{source.title}"
            )
            print(
                f"           {source.url}"
            )

        print(
            "[SOURCE] extracted:",
            len(sources),
        )

        return sources

    def _extract_search_queries(
            self,
            answer_wrap: Locator,
    ) -> list[str]:
        workflow = answer_wrap.locator(
            RESEARCH_WORKFLOW_SELECTOR
        )

        print(
            "[SEARCH] workflow count:",
            workflow.count(),
        )

        if workflow.count() == 0:
            return []

        result: list[str] = []
        seen: set[str] = set()

        for workflow_index in range(
                workflow.count()
        ):
            current_workflow = (
                workflow.nth(
                    workflow_index
                )
            )

            search_sections = (
                current_workflow.evaluate(
                    """
                    root => {
                        const titlePattern =
                            /^搜索\\s*(\\d+)\\s*个关键词，参考\\s*(\\d+)\\s*篇资料$/;

                        const sections = [];

                        const spans =
                            Array.from(
                                root.querySelectorAll(
                                    "span"
                                )
                            );

                        for (
                            const heading of spans
                        ) {
                            const headingText =
                                (
                                    heading.innerText ||
                                    heading.textContent ||
                                    ""
                                ).trim();

                            const match =
                                headingText.match(
                                    titlePattern
                                );

                            if (!match) {
                                continue;
                            }

                            /*
                             * DOM 结构：
                             *
                             * section
                             * ├─ header
                             * │   └─ span:
                             * │      搜索 3 个关键词...
                             * │
                             * └─ content
                             *     ├─ query container
                             *     │   ├─ span query 1
                             *     │   ├─ span query 2
                             *     │   └─ span query 3
                             *     │
                             *     └─ source container
                             */

                            const header =
                                heading.parentElement;

                            const content =
                                header
                                    ?.nextElementSibling;

                            const queryContainer =
                                content
                                    ?.firstElementChild;

                            if (!queryContainer) {
                                continue;
                            }

                            const queries = [];

                            for (
                                const child of
                                Array.from(
                                    queryContainer
                                        .children
                                )
                            ) {
                                if (
                                    child.tagName
                                    !== "SPAN"
                                ) {
                                    continue;
                                }

                                let text =
                                    (
                                        child.innerText ||
                                        child.textContent ||
                                        ""
                                    ).trim();

                                /*
                                 * 千问目前展示：
                                 * "搜索关键词"
                                 *
                                 * 去掉外层引号。
                                 */
                                text = text.replace(
                                    /^[\\"“”']+|[\\"“”']+$/g,
                                    ""
                                ).trim();

                                if (text) {
                                    queries.push(
                                        text
                                    );
                                }
                            }

                            sections.push({
                                expected_query_count:
                                    Number(
                                        match[1]
                                    ),

                                source_count:
                                    Number(
                                        match[2]
                                    ),

                                queries
                            });
                        }

                        return sections;
                    }
                    """
                )
            )

            for section in search_sections:
                expected = section[
                    "expected_query_count"
                ]

                queries = section[
                    "queries"
                ]

                print(
                    "[SEARCH] expected:",
                    expected,
                )

                print(
                    "[SEARCH] extracted in section:",
                    len(queries),
                )

                if (
                        expected
                        != len(queries)
                ):
                    print(
                        "[SEARCH] warning: "
                        "query count mismatch"
                    )

                for query in queries:
                    query = (
                        query.strip()
                    )

                    if not query:
                        continue

                    if query in seen:
                        continue

                    seen.add(
                        query
                    )

                    result.append(
                        query
                    )

                    print(
                        f"[SEARCH {len(result)}]",
                        query,
                    )

        print(
            "[SEARCH] extracted total:",
            len(result),
        )

        return result

    # =========================================
    # 主入口
    # =========================================

    def ask(
            self,
            question: str,
            *,
            mode: str = "quick",
            new_chat: bool = True,
            answer_timeout_seconds: int = 60,
    ) -> QwenAnswerResult:
        self.ensure_no_risk_control()

        question = question.strip()

        if not question:
            raise ValueError(
                "question 不能为空"
            )

        # 1. 是否新建独立对话
        if new_chat:
            self.new_chat()

            self.page.wait_for_timeout(
                NEW_CHAT_SETTLE_MS
            )

        # 2. 明确保证当前模式正确
        self.set_mode(
            mode
        )

        self.page.wait_for_timeout(
            MODE_SETTLE_MS
        )

        # 3. 获取当前可见输入框
        input_box = self._first_visible(
            self.page.locator(
                INPUT_SELECTOR
            )
        )

        if input_box is None:
            raise QwenElementNotFoundError(
                "没有找到千问输入框"
            )

        # 4. 记录发送前已有 turn_id
        previous_turn_ids = (
            self._get_turn_ids()
        )

        # 5. 填写问题
        input_box.fill(
            question
        )

        self.page.wait_for_timeout(
            INPUT_SETTLE_MS
        )

        try:
            current_input_text = (
                input_box
                .inner_text()
                .strip()
            )
        except Exception:
            current_input_text = ""

        print(
            "[INPUT]",
            repr(current_input_text),
        )

        # 6. 等待当前发送按钮真正变为 enabled
        send_button = (
            self._wait_for_send_button_enabled(
                timeout_seconds=8,
            )
        )

        self.page.wait_for_timeout(
            BEFORE_SEND_MS
        )

        self.ensure_no_risk_control()

        # 7. 发送
        send_button.click()

        # 8. 等待新 turn
        turn_id = (
            self._wait_for_new_turn(
                previous_turn_ids
            )
        )

        # 9. 获取页面中的实际问题正文
        question_wrap = (
            self.page.locator(
                f'[data-chat-question-wrap="{turn_id}"]'
            )
        )

        actual_question = (
            question_wrap.locator(
                QUESTION_TEXT_SELECTOR
            )
            .inner_text()
            .strip()
        )

        # 10. 等待正式回答完成
        answer = self._wait_for_answer(
            turn_id,
            timeout_seconds=answer_timeout_seconds,
        )

        self.page.wait_for_timeout(
            ANSWER_SETTLE_MS
        )

        # 11. Research 模式展开并提取来源
        answer_wrap = self.page.locator(
            f'[data-chat-answers-wrap="{turn_id}"]'
        )

        sources: list[QwenSource] = []
        search_queries: list[str] = []

        if mode == "quick":
            sources = (
                self._extract_quick_sources(
                    answer_wrap
                )
            )

        elif mode == "research":
            # 先提取搜索关键词
            search_queries = (
                self._extract_search_queries(
                    answer_wrap
                )
            )

            # 再展开全部来源
            self._expand_research_sources(
                answer_wrap
            )

            # 最后提取来源
            sources = self._extract_sources(
                answer_wrap
            )

        # 12. 返回结构化结果
        return QwenAnswerResult(
            question=actual_question,
            answer=answer,
            turn_id=turn_id,
            chat_url=self.page.url,
            mode=mode,
            mode_label=MODE_VALUES[mode],
            search_queries=search_queries,
            sources=sources,
        )

    # =========================================
    # 模式
    # =========================================

    def get_mode(self) -> str:
        locator = self.page.locator(
            MODE_MENU_BUTTON_SELECTOR
        )

        for index in range(
                locator.count()
        ):
            item = locator.nth(index)

            try:
                if not item.is_visible():
                    continue

                label = item.get_attribute(
                    "aria-label"
                )

                for mode, mode_label in (
                        MODE_VALUES.items()
                ):
                    if label == mode_label:
                        return mode

            except Exception:
                continue

        raise QwenModeError(
            "无法识别当前千问模式"
        )

    def set_mode(
            self,
            mode: str,
            timeout_seconds: int = 5,
    ) -> None:
        self.ensure_no_risk_control()

        if mode not in MODE_VALUES:
            raise ValueError(
                f"不支持的千问模式: {mode}"
            )

        current_mode = self.get_mode()

        if current_mode == mode:
            return

        target_label = MODE_VALUES[
            mode
        ]

        mode_button = None

        locator = self.page.locator(
            MODE_MENU_BUTTON_SELECTOR
        )

        for index in range(
                locator.count()
        ):
            item = locator.nth(index)

            try:
                if not item.is_visible():
                    continue

                label = (
                    item.get_attribute(
                        "aria-label"
                    )
                )

                if label in (
                        MODE_VALUES.values()
                ):
                    mode_button = item
                    break

            except Exception:
                continue

        if mode_button is None:
            raise QwenModeError(
                "没有找到模式菜单按钮"
            )

        mode_button.click()

        self.page.wait_for_timeout(
            200
        )

        option_locator = (
            self.page.get_by_text(
                target_label,
                exact=True,
            )
        )

        option = self._first_visible(
            option_locator
        )

        if option is None:
            raise QwenModeError(
                f"没有找到模式选项: "
                f"{target_label}"
            )

        option.click()

        start = time.monotonic()

        while (
                time.monotonic() - start
                < timeout_seconds
        ):
            self.ensure_no_risk_control()

            try:
                if self.get_mode() == mode:
                    return
            except QwenModeError:
                pass

            self.page.wait_for_timeout(
                100
            )

        raise QwenModeError(
            f"模式切换失败: "
            f"{current_mode} -> {mode}"
        )
