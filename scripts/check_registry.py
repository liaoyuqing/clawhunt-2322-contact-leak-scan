"""CI 第一步：只做路由枚举与登记比对，失败时打印 UNDECLARED_ENDPOINT。

单独成步的价值：pytest 跑几百条用例要几十秒，这一步 1 秒内就能告诉你是「漏登记」
还是「响应里真有联系方式」，CI 日志一眼可辨。
"""
from __future__ import annotations

import sys

from app.main import create_app
from scan import enumerate as route_enum
from scan.registry import stale, undeclared


def main() -> int:
    app = create_app()
    found = set(route_enum.enumerate_templates(app))
    missing = undeclared(found)
    gone = stale(found)
    counts = route_enum.prefix_report(app)
    for prefix, count in counts.items():
        print(f"{prefix}: {count}")
    print(f"total_templates={len(found)}")
    if gone:
        print("WARN_STALE_ENDPOINT: " + ", ".join(gone))
    if missing:
        print("UNDECLARED_ENDPOINT: " + ", ".join(missing))
        return 1
    print("registry_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
