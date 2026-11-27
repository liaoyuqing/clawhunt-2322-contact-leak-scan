"""报告生成：每条路由模板 × 每种身份一行，扫描响应 JSON，落 Markdown。

行数恒等于「接口数 × 身份数」——被 403 拒绝、405、空响应体都照样占一行，
只在「结果」列写明原因，不省略行（否则 AC3 的算术断言就失去意义）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fastapi.testclient import TestClient

from app.identity import IDENTITIES
from scan import enumerate as route_enum
from scan import whitelist
from scan.leak_check import scan_payload

REPORT_PATH = Path(__file__).resolve().parent.parent / "reports" / "report.md"

# 路由模板里 {param} 的取值：一律取虚构数据集里的真实主键，
# 保证接口走的是「查到了」的分支，而不是 404 分支（404 的响应体里没有业务字段，扫了也没有意义）。
PATH_VALUES = {
    "event_id": "evt-1001",
    "signup_id": "sg-1001",
    "ticket_key": "tk-1001",
    "questionnaire_id": "q-1001",
    "post_id": "p-1001",
    "faq_id": "faq-01",
    "case_id": "c-1001",
    "task_id": "t-1001",
    "template_id": "tmpl-activity",
}

# 需要请求体的接口：给最小合法 JSON（字段值全部取自虚构数据集）。
BODIES = {
    ("POST", "/api/mini/signups"): {"event_id": "evt-1001"},
    ("POST", "/api/mini/support/handoff"): {"case_id": "c-1001", "reason": "member_requested"},
}


@dataclass
class Row:
    route: str
    method: str
    identity: str
    status_code: int
    verdict: str
    field_paths: str
    scanned_nodes: int = 0


@dataclass
class Report:
    rows: list[Row] = field(default_factory=list)
    allow_hits: list = field(default_factory=list)

    @property
    def endpoints(self) -> list[tuple[str, str]]:
        """接口 = (方法, 路由模板)。同一模板上的 GET 与 POST 是两个接口，各要两行。"""
        return sorted({(row.method, row.route) for row in self.rows})

    @property
    def interfaces(self) -> list[str]:
        return sorted({row.route for row in self.rows})

    @property
    def hit_count(self) -> int:
        return sum(1 for row in self.rows if row.verdict == "LEAK")


def concrete_path(template: str) -> str:
    path = template
    for name, value in PATH_VALUES.items():
        path = path.replace("{" + name + "}", value)
    return path


def _call(client: TestClient, method: str, template: str, identity: str):
    url = concrete_path(template)
    headers = {"X-Mini-Identity": identity}
    body = BODIES.get((method, template))
    return client.request(method, url, headers=headers, json=body)


def build_report(app) -> Report:
    client = TestClient(app)
    report = Report()
    routes = route_enum.enumerate_routes(app)
    for template in sorted(routes):
        for method in sorted(routes[template]):
            for identity in IDENTITIES:
                response = _call(client, method, template, identity)
                if response.status_code >= 400:
                    report.rows.append(Row(template, method, identity, response.status_code, "NOT_ALLOWED", "-"))
                    continue
                try:
                    payload = response.json()
                except ValueError:
                    report.rows.append(Row(template, method, identity, response.status_code, "EMPTY_BODY", "-"))
                    continue
                scan = scan_payload(payload, route=template)
                report.allow_hits.extend(scan.allowed)
                if scan.ok:
                    verdict = "PASS"
                    field_paths = "-"
                else:
                    verdict = "LEAK"
                    field_paths = "; ".join(sorted({hit.field_path for hit in scan.hits}))
                report.rows.append(
                    Row(template, method, identity, response.status_code, verdict, field_paths, scan.scanned_nodes)
                )
    return report


def render_markdown(report: Report) -> str:
    interfaces = report.interfaces
    endpoints = report.endpoints
    lines = [
        "# 联系方式泄露扫描报告（虚构数据）",
        "",
        "生成方式：`python -m scripts.build_report`。本文件由脚本产出，不要手改。",
        "",
        "口径说明：接口 =（方法, 路由模板），同一模板上的 GET 与 POST 各自算一个接口，",
        "每个接口必须有 member 与 staff 两行。",
        "",
        "## 汇总",
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 路由模板数 | {len(interfaces)} |",
        f"| 接口数（方法 + 路径） | {len(endpoints)} |",
        f"| 身份数 | {len(IDENTITIES)} |",
        f"| 报告行数 | {len(report.rows)} |",
        f"| 期望行数（接口数 × 2） | {len(endpoints) * 2} |",
        f"| 泄露行数 | {report.hit_count} |",
        f"| 白名单放行条目数 | {len(report.allow_hits)} |",
        "",
        "## 逐接口 × 身份结果",
        "",
        "列含义：接口 = FastAPI 路由模板；身份 = member / staff；结果 = PASS / LEAK / NOT_ALLOWED / EMPTY_BODY；命中字段路径 = JSON 路径，PASS 时为 -。",
        "",
        "| 接口 | 方法 | 身份 | 结果 | 命中字段路径 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report.rows:
        lines.append(
            f"| `{row.route}` | {row.method} | {row.identity} | {row.verdict} | `{row.field_paths}` |"
        )
    lines += [
        "",
        "## 数字串白名单（显式登记，放行原因逐条列出）",
        "",
        "| 路由模板 | 字段路径后缀 | 正则 | 放行原因 |",
        "| --- | --- | --- | --- |",
    ]
    for rule in whitelist.describe():
        lines.append(
            f"| `{rule['route']}` | `{rule['field_suffix']}` | `{rule['pattern']}` | {rule['reason']} |"
        )
    lines += ["", "### 本次运行实际命中白名单的字段", "", "| 路由模板 | 字段路径 | 值 | 原因 |", "| --- | --- | --- | --- |"]
    if report.allow_hits:
        for hit in report.allow_hits:
            lines.append(f"| `{hit.route}` | `{hit.field_path}` | `{hit.masked}` | {hit.reason} |")
    else:
        lines.append("| - | - | - | 本次运行没有字段命中白名单（票号字段未出现在被扫响应里时属正常） |")
    lines += [
        "",
        "## 判定口径",
        "",
        "- 键名黑名单（不区分大小写、含嵌套层）：phone / mobile / tel / email / wechat / wx_id / qq / contact。",
        "- 值正则：11 位大陆手机号 `1[3-9]\\d{9}`；带区号座机 `0\\d{2,3}-?\\d{7,8}`；邮箱；`wxid_` 前缀。",
        "- 掩码判不合格：前三后四 `1[3-9]\\d\\*{2,}\\d{4}`、只留后四位 `\\*{3,}\\d{4}`、只留前三位 `1[3-9]\\d\\*{3,}`。",
        "- 递归限制：深度上限 8 层，栈内 id() 去环；超限与环路本身记一条命中（该段视为未扫描）。",
        "",
    ]
    return "\n".join(lines)


def write_report(app, path: Path = REPORT_PATH) -> Report:
    report = build_report(app)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")
    return report
