"""构建 reports/report.md（接口 × 身份全量扫描）。

输出四个数字，口径写死在这里，正文与证据日志都引用同一行：
  templates = 路由模板数（不含方法）
  endpoints = 接口数 = 模板 × 方法（GET/POST 各算一个）
  rows      = 报告行数 = endpoints × 身份数
  leaks     = 泄露行数，必须为 0
"""
from __future__ import annotations

from app.main import create_app
from scan.report import REPORT_PATH, write_report


def main() -> int:
    report = write_report(create_app())
    print(
        "templates=%d endpoints=%d rows=%d leaks=%d allowlisted=%d"
        % (
            len(report.interfaces),
            len(report.endpoints),
            len(report.rows),
            report.hit_count,
            len(report.allow_hits),
        )
    )
    print("written:", REPORT_PATH.name)
    return 0 if report.hit_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
