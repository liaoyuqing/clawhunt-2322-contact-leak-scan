"""统一响应外壳：{"data": ..., "meta": {...}}。

扫描器和报告都以这个外壳为根，字段路径因此形如 data.items[0].contact_phone。
"""
from __future__ import annotations

from typing import Any


def envelope(data: Any, **meta: Any) -> dict:
    body: dict[str, Any] = {"data": data}
    if meta:
        body["meta"] = meta
    return body
