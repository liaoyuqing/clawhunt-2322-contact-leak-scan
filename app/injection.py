"""故障注入开关：仅供负面测试使用，生产路径恒为空操作。

扫描器的负面测试需要「让某个接口故意返回带联系方式的 JSON」，
但不能改路由源码，于是每个路由在返回前调用 apply_override(path, body)：
override 为空时原样返回，测试注册了 override 时返回被注入的 body。
测试结束后必须 clear()（tests/conftest.py 的 autouse fixture 负责）。
"""
from __future__ import annotations

from typing import Any

_OVERRIDES: dict[str, Any] = {}


def register(path: str, body: Any) -> None:
    _OVERRIDES[path] = body


def clear() -> None:
    _OVERRIDES.clear()


def active() -> dict[str, Any]:
    return dict(_OVERRIDES)


def apply_override(path: str, body: Any) -> Any:
    return _OVERRIDES.get(path, body)
