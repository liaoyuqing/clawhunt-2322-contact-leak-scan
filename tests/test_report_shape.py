"""AC3：报告中每个接口都有会员身份与员工身份两行结果。

断言口径全部算术化：行数 == 接口数 × 2；每个接口恰有 member 与 staff 各一行；
被 403 拒绝的接口照样占两行（结果列写 NOT_ALLOWED，不省略）。
"""
from __future__ import annotations

import re

import pytest

from app.identity import IDENTITIES
from scan import enumerate as route_enum
from scan.report import build_report


@pytest.fixture(scope="module")
def report():
    from app.main import create_app

    return build_report(create_app())


def test_row_count_equals_endpoints_times_two(report):
    assert len(report.rows) == len(report.endpoints) * 2


def test_every_endpoint_has_both_identities(report):
    seen: dict[tuple[str, str], set[str]] = {}
    for row in report.rows:
        seen.setdefault((row.method, row.route), set()).add(row.identity)
    for key, identities in seen.items():
        assert identities == set(IDENTITIES), f"{key} 缺少身份行：{identities}"


def test_report_covers_every_enumerated_endpoint(report, app):
    routes = route_enum.enumerate_routes(app)
    expected = {(method, template) for template, methods in routes.items() for method in methods}
    assert {(row.method, row.route) for row in report.rows} == expected


def test_denied_endpoint_still_keeps_both_rows(report):
    rows = [row for row in report.rows if row.route == "/api/mini/me/profile"]
    assert len(rows) == 2
    verdicts = {row.identity: row.verdict for row in rows}
    assert verdicts["member"] == "PASS"
    assert verdicts["staff"] == "NOT_ALLOWED"


def test_staff_only_endpoint_keeps_both_rows(report):
    rows = [row for row in report.rows if row.route == "/api/mini/staff/profile"]
    assert len(rows) == 2
    verdicts = {row.identity: row.verdict for row in rows}
    assert verdicts["staff"] == "PASS"
    assert verdicts["member"] == "NOT_ALLOWED"


def test_no_leak_rows_in_baseline(report):
    assert report.hit_count == 0


def test_rendered_markdown_row_count(report):
    from scan.report import render_markdown

    text = render_markdown(report)
    table_rows = [
        line
        for line in text.splitlines()
        if re.match(r"^\| `?/api/mini/\S*`? \| (GET|POST) \|", line)
    ]
    assert len(table_rows) == len(report.endpoints) * 2


def test_markdown_has_four_result_columns(report):
    from scan.report import render_markdown

    text = render_markdown(report)
    header = next(line for line in text.splitlines() if line.startswith("| 接口 |"))
    assert header.count("|") == 6, header
    assert "身份" in header and "结果" in header and "命中字段路径" in header


def test_markdown_lists_allowlist_rules(report):
    from scan.report import render_markdown

    text = render_markdown(report)
    assert "数字串白名单" in text
    assert "ticket_no" in text


def test_summary_line_reports_totals(report):
    from scan.report import render_markdown

    text = render_markdown(report)
    assert f"| 接口数（方法 + 路径） | {len(report.endpoints)} |" in text
    assert f"| 报告行数 | {len(report.rows)} |" in text
