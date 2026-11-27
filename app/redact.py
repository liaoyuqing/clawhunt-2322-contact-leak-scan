"""接口桩侧的出参脱敏：把自由文本里的联系方式样例替换成固定遮蔽串。

该模块只服务于接口桩本身（把虚构数据集里的联系方式样例裁掉），
扫描器 scan/leak_check.py 有自己独立的一套判定正则，二者不共用同一份实现，
避免「用被测对象的判定逻辑给自己打分」。
"""
from __future__ import annotations

import re

MASK_TEXT = "【联系方式已隐藏】"

_PATTERNS = (
    re.compile(r"1[3-9]\d{9}"),            # 11 位大陆手机号
    re.compile(r"0\d{2,3}-?\d{7,8}"),     # 带区号座机
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # 邮箱
    re.compile(r"wxid_[0-9a-zA-Z]+"),      # 微信号
    re.compile(r"1[3-9]\d\*{2,}\d{4}"),      # 前三后四掩码
    re.compile(r"\d{3}\*{4,}"),             # 只留前三位
)


def redact_text(text: str) -> str:
    """把自由文本里的联系方式样例整体替换为遮蔽串。

    匹配到的整段（含掩码片段）一次替换，避免留下 138**** 这类残段。
    """
    if not isinstance(text, str):
        return text
    cleaned = text
    for pattern in _PATTERNS:
        cleaned = pattern.sub(MASK_TEXT, cleaned)
    return cleaned


def redact_deep(value, depth: int = 0):
    """递归脱敏：只改字符串值，保持结构不变。"""
    if depth > 12:
        return value
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_deep(item, depth + 1) for item in value]
    if isinstance(value, dict):
        return {key: redact_deep(item, depth + 1) for key, item in value.items()}
    return value

