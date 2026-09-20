class QwenCollectorError(RuntimeError):
    """千问采集器基础异常。"""


class QwenConnectionError(QwenCollectorError):
    """无法连接千问浏览器。"""


class QwenElementNotFoundError(QwenCollectorError):
    """关键页面元素不存在。"""


class QwenRiskControlError(QwenCollectorError):
    """千问真人验证 / 风控。"""


class QwenRefusalError(QwenCollectorError):
    """Qwen始终拒绝回应。"""


class QwenTimeoutError(QwenCollectorError):
    """等待页面状态超时。"""


class QwenModeError(QwenCollectorError):
    """千问模式识别或切换失败。"""


class QwenQuotaExhaustedError(QwenCollectorError):
    """Qwen account quota exhausted."""
