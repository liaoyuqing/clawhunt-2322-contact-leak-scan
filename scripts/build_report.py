"""构建 reports/report.md（接口 × 身份全量扫描）。"""
from __future__ import annotations

from app.main import create_app
from scan.report import REPORT_PATH, write_report


def main() -> int:
    report = write_report(create_app())
    print("interfaces=%d rows=%d leaks=%d allowlisted=%d" % (
        len(report.interfaces), len(report.rows), report.hit_count, len(report.allow_hits)))
    print("written:", REPORT_PATH)
    return 0 if report.hit_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
