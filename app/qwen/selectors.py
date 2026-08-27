QWEN_DOMAIN = "qianwen.com"

INPUT_SELECTOR = (
    '[role="textbox"]'
    '[data-slate-editor="true"]'
    '[contenteditable="true"]'
)

SEND_BUTTON_SELECTOR = (
    'button[aria-label="发送消息"]'
)

QUESTION_WRAP_SELECTOR = (
    "[data-chat-question-wrap]"
)

QUESTION_TEXT_SELECTOR = (
    ".question-text-card"
)

ANSWER_WRAP_SELECTOR = (
    "[data-chat-answers-wrap]"
)

ANSWER_MARKDOWN_SELECTOR = (
    ".qk-markdown"
)

ANSWER_COMPLETE_SELECTOR = (
    ".qk-markdown-complete"
)

ANSWER_FEEDBACK_SELECTOR = (
    '[data-answer-feedback-toolbar="true"]'
)

MODE_MENU_BUTTON_SELECTOR = (
    'button[aria-haspopup="menu"]'
)

RISK_CONTROL_TEXTS = (
    "请拖动下方滑块完成验证",
    "通过验证以确保正常访问",
    "验证失败",
)

MODE_VALUES = {
    "quick": "快速",
    "research": "思考研究",
}

ANSWER_FINAL_SELECTOR = (
    ".answer-common-card .qk-markdown"
)

RESEARCH_WORKFLOW_SELECTOR = (
    '[data-card_name="bar_workflow"]'
)

SOURCE_LINK_SELECTOR = (
    'a[href^="http"]'
)
