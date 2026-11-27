"""一键重采集 docs/checks/ 下四份验收日志 + 全量测试日志 + 报告构建日志。

用法（仓库根目录）：
    python -m scripts.capture_checks

每份日志都是「注入故障 -> 观察到预期失败 -> 清掉故障 -> 观察到恢复」三段，
不手工编辑任何日志内容，本脚本就是日志的唯一来源。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKS = ROOT / "docs" / "checks"
REPORT = ROOT / "reports" / "report.md"
WORKFLOW = ROOT / ".github" / "workflows" / "leak-scan.yml"

ALLOW_ENV = "LEAK_DEMO_ALLOW"
EXTRA_ROUTE_ENV = "LEAK_DEMO_EXTRA_ROUTE"
LEAK_ENV = "LEAK_DEMO_LEAK"
PROBE_ROUTE = "/api/mini/events/__leak_probe"
LEAK_ROUTE = "/api/mini/support/tickets"
LEAK_CASE = "tests/test_api_surface.py::test_endpoint_has_no_contact_leak[GET-/api/mini/support/tickets-member]"
GUARD_CASE = "tests/test_api_surface.py::test_every_template_is_registered"


def run(args: list[str]) -> tuple[int, str]:
    env = dict(os.environ)
    # 子进程输出一律按 UTF-8 出来，否则中文注释在日志里会被本地代码页截坏。
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    );
    combined = (completed.stdout or "") + (completed.stderr or "");
    return completed.returncode, combined.rstrip()


def write(name: str, lines: list[str]) -> Path:
    CHECKS.mkdir(parents=True, exist_ok=True)
    path = CHECKS / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def report_rows() -> list[str]:
    text = REPORT.read_text(encoding="utf-8")
    pattern = re.compile(r"^\| `?/api/mini/\S*`? \| (?:GET|POST) \|")
    return [line for line in text.splitlines() if pattern.match(line)]


def capture_ac1() -> list[str]:
    out = [
        "# AC1 演示：人为新增一个未登记用例的接口，登记比对与 pytest 守卫必须失败",
        "# 全程只设环境变量，不改任何源码；清掉变量即恢复基线。",
        "# 演示开关有两道闸：必须同时设 LEAK_DEMO_ALLOW=1，且不在 CI 环境里。",
        "# 复现命令（PowerShell）：",
        "#   $" + "env:LEAK_DEMO_ALLOW = " + chr(34) + "1" + chr(34),
        "#   $" + "env:LEAK_DEMO_EXTRA_ROUTE = " + chr(34) + PROBE_ROUTE + chr(34),
        "#   python -m scripts.check_registry",
        "#   python -m pytest " + GUARD_CASE + " -q",
        "#   Remove-Item Env:LEAK_DEMO_EXTRA_ROUTE",
        "#   Remove-Item Env:LEAK_DEMO_ALLOW",
        "",
    ]
    os.environ[ALLOW_ENV] = "1"
    os.environ[EXTRA_ROUTE_ENV] = PROBE_ROUTE
    try:
        code_a, text_a = run(["-m", "scripts.check_registry"])
        code_b, text_b = run(["-m", "pytest", GUARD_CASE, "-q"])
    finally:
        os.environ.pop(EXTRA_ROUTE_ENV, None)
        os.environ.pop(ALLOW_ENV, None)
    code_c, text_c = run(["-m", "pytest", GUARD_CASE, "-q"])
    out += ["===== 1) 注入后 python -m scripts.check_registry =====", text_a, "EXIT_CODE=" + str(code_a), ""]
    out += ["===== 2) 注入后 pytest 守卫用例（应失败） =====", text_b, "EXIT_CODE=" + str(code_b), ""]
    out += ["===== 3) 恢复基线后同一命令（应通过） =====", text_c, "EXIT_CODE=" + str(code_c)]
    return out


def capture_ac2() -> list[str]:
    out = [
        "# AC2 演示：人为让 " + LEAK_ROUTE + " 返回一个虚构手机号，扫描必须失败",
        "# 失败文本里必须同时出现接口路径（path=）与字段路径（field=）。",
        "# 同样受两道闸约束：需 LEAK_DEMO_ALLOW=1，且 CI 环境下不生效。",
        "# 复现命令（PowerShell）：",
        "#   $" + "env:LEAK_DEMO_ALLOW = " + chr(34) + "1" + chr(34),
        "#   $" + "env:LEAK_DEMO_LEAK = " + chr(34) + LEAK_ROUTE + chr(34),
        "#   python -m pytest " + LEAK_CASE + " -q",
        "#   python -m scripts.build_report",
        "#   Remove-Item Env:LEAK_DEMO_LEAK",
        "#   Remove-Item Env:LEAK_DEMO_ALLOW",
        "",
    ]
    os.environ[ALLOW_ENV] = "1"
    os.environ[LEAK_ENV] = LEAK_ROUTE
    try:
        code_a, text_a = run(["-m", "pytest", LEAK_CASE, "-q"])
        code_b, text_b = run(["-m", "scripts.build_report"])
        leak_lines = [line for line in report_rows() if "LEAK" in line]
    finally:
        os.environ.pop(LEAK_ENV, None)
        os.environ.pop(ALLOW_ENV, None)
    code_c, text_c = run(["-m", "pytest", LEAK_CASE, "-q"])
    code_d, text_d = run(["-m", "scripts.build_report"])
    out += ["===== 1) 注入后跑目标接口（应失败） =====", text_a, "EXIT_CODE=" + str(code_a), ""]
    out += ["===== 2) 注入后重建报告，该接口两行应记为 LEAK =====", text_b, "EXIT_CODE=" + str(code_b)]
    out += ["===== 报告里该接口的行 =====", *leak_lines, ""]
    out += ["===== 3) 恢复基线后同一命令（应通过，报告回到 0 泄露） =====", text_c, "EXIT_CODE=" + str(code_c)]
    out += [text_d, "EXIT_CODE=" + str(code_d)]
    return out


def capture_ac3() -> list[str]:
    out = [
        "# AC3 演示：报告里每个接口都有会员身份与员工身份两行结果",
        "# 复现命令：python -m scripts.build_report，然后统计 report.md 结果表的行数",
        "",
    ]
    code, text = run(["-m", "scripts.build_report"])
    rows = report_rows()
    routes = sorted({row.split("|")[1].strip() for row in rows})
    member = [row for row in rows if "| member |" in row]
    staff = [row for row in rows if "| staff |" in row]
    out += ["===== 1) 重建报告 =====", text, "EXIT_CODE=" + str(code), ""]
    out += [
        "===== 2) 结果表行数统计 =====",
        "result_rows=" + str(len(rows)),
        "distinct_routes=" + str(len(routes)),
        "member_rows=" + str(len(member)),
        "staff_rows=" + str(len(staff)),
        "",
    ]
    out.append("===== 3) 逐接口核对（接口 = 方法 + 路径）：每个接口是否 member / staff 各一行 =====")
    endpoints = sorted({"|".join([row.split("|")[2].strip(), row.split("|")[1].strip()]) for row in rows})
    out.append("endpoints_method_path=" + str(len(endpoints)))
    for endpoint in endpoints:
        method, route = endpoint.split("|", 1)
        per = [row for row in rows if row.split("|")[1].strip() == route and row.split("|")[2].strip() == method]
        identities = sorted(row.split("|")[3].strip() for row in per)
        status = "OK" if identities == ["member", "staff"] else "MISSING"
        out.append(method + " " + route + " -> " + ",".join(identities) + " (rows=" + str(len(per)) + ") " + status)
    out.append("")
    out.append("===== 4) 身份受限接口仍保留两行（NOT_ALLOWED 不省略） =====")
    text_report = REPORT.read_text(encoding="utf-8")
    out += [line for line in text_report.splitlines() if "NOT_ALLOWED" in line and line.startswith("| `")]
    return out


def capture_ac4() -> list[str]:
    yml = WORKFLOW.read_text(encoding="utf-8")
    out = [
        "# AC4 证据：CI 配置中该测试失败会阻断合并",
        "# （1）工作流全文与关键行计数；（2）本地按 CI 同样的事件序列复跑，证明退出码会变成非 0",
        "",
        "===== 1) .github/workflows/leak-scan.yml 全文 =====",
        yml.rstrip(),
        "",
        "===== 2) 关键断言 =====",
        "pull_request_trigger=" + str("pull_request:" in yml),
        "pytest_step_count=" + str(yml.count("python -m pytest tests/ -q")),
        "continue_on_error_count=" + str(yml.count("continue-on-error")),
        "exit_code_swallow_count=" + str(yml.count("|| true") + yml.count("; true")),
        "",
        "===== 3) 模拟 CI 步骤：注入一条泄露后跑同一命令，退出码必须非 0 =====",
    ]
    os.environ[ALLOW_ENV] = "1"
    os.environ[LEAK_ENV] = LEAK_ROUTE
    try:
        code_a, text_a = run(["-m", "scripts.check_registry"])
        code_b, text_b = run(["-m", "pytest", "tests/", "-q"])
    finally:
        os.environ.pop(LEAK_ENV, None)
        os.environ.pop(ALLOW_ENV, None)
    tail = text_b.splitlines()[-4:]
    out += ["check_registry_exit=" + str(code_a), *tail, "pytest_exit=" + str(code_b)]
    out.append("=> step 失败 -> job leak-scan 失败 -> PR 必过检查不满足，合并按钮禁用")
    out.append("")
    out.append("===== 4) 恢复基线后同样命令，退出码必须为 0 =====")
    code_c, _ = run(["-m", "scripts.check_registry"])
    code_d, text_d = run(["-m", "pytest", "tests/", "-q"])
    out += ["check_registry_exit=" + str(code_c), text_d.splitlines()[-1], "pytest_exit=" + str(code_d)]
    return out


def main() -> int:
    paths = []
    paths.append(write("ac1-unguarded-route.log", capture_ac1()))
    paths.append(write("ac2-leak-detected.log", capture_ac2()))
    paths.append(write("ac3-report-shape.log", capture_ac3()))
    paths.append(write("ac4-ci-blocking.log", capture_ac4()))
    code_full, text_full = run(["-m", "pytest", "tests/", "-v"])
    paths.append(write("pytest-full.log", text_full.splitlines()))
    code_report, text_report = run(["-m", "scripts.build_report"])
    paths.append(write("report-build.log", text_report.splitlines()))
    for path in paths:
        print("wrote", path.relative_to(ROOT))
    print("pytest_exit=" + str(code_full) + " report_exit=" + str(code_report))
    print(text_full.splitlines()[-1])
    return 0 if code_full == 0 and code_report == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())


