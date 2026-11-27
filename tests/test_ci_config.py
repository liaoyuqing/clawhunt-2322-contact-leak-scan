"""AC4：CI 配置里该测试失败会阻断合并。

这里不靠人眼看 yml，而是把 yml 当数据断言：
1. 存在 leak-scan job；
2. 触发条件里有 pull_request（PR 合并前的门禁）；
3. 真的跑了 python -m pytest tests/；
4. 全文没有 continue-on-error（否则失败会被吞掉）；
5. 没有把 pytest 的退出码用 || true / ; true 抹平。

分支保护（required status checks）是仓库设置项，不在 yml 里，README 单独写了配置步骤。
"""
from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "leak-scan.yml"


@pytest.fixture(scope="module")
def workflow_text() -> str:
    assert WORKFLOW.is_file(), f"缺少 CI 配置：{WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_file_exists_and_is_utf8(workflow_text):
    assert workflow_text.startswith("name: leak-scan")


def test_workflow_triggers_on_pull_request(workflow_text):
    assert "pull_request:" in workflow_text


def test_workflow_runs_pytest_on_tests_dir(workflow_text):
    assert "python -m pytest tests/ -q" in workflow_text


def test_workflow_has_no_continue_on_error(workflow_text):
    assert "continue-on-error" not in workflow_text, "continue-on-error 会让失败的扫描被忽略"


@pytest.mark.parametrize("escape", ["|| true", "; true", "|| exit 0"])
def test_workflow_does_not_swallow_exit_code(workflow_text, escape):
    assert escape not in workflow_text


def test_workflow_job_is_named_leak_scan(workflow_text):
    assert "jobs:" in workflow_text
    assert "  leak-scan:" in workflow_text


def test_workflow_has_bounded_runtime(workflow_text):
    assert "timeout-minutes:" in workflow_text


def test_workflow_registry_step_runs_before_pytest(workflow_text):
    registry_at = workflow_text.index("python -m scripts.check_registry")
    pytest_at = workflow_text.index("python -m pytest tests/ -q")
    assert registry_at < pytest_at, "枚举比对应在完整测试之前，先给出漏登记的直接原因"
