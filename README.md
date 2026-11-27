# 会员端接口联系方式泄露扫描 · pytest 回归 + CI 门禁

小程序会员端的活动、报名、电子票、问卷、航海日志、FAQ、转人工、管家、订阅消息、隐私与注销接口，
以及员工端接口，逐个以「会员」「员工」两种身份调用，递归扫描响应 JSON，
禁止出现任何手机号、座机、邮箱、微信号、QQ 等联系方式——包括 `138****8000` 这类部分掩码形式。

> 本仓库所有数据均为**虚构样例**：手机号取 138/139/137/136 示意号段，座机取 021/0755/010 区号，
> 邮箱统一 `example.com` 域名，微信号为 `wxid_` 虚构串。不对应任何真实个人、真实企业或真实客户。

## 一、依赖与运行环境

| 项 | 要求 |
| --- | --- |
| Python | 3.11 及以上（开发与验证用 3.11.9） |
| 依赖包 | fastapi 0.136.1、httpx 0.28.1、pydantic 2.14.4、pytest 9.2.0（见 `requirements.txt`） |
| 数据库 | 不需要。接口桩只读 `fixtures/dataset.json` |
| 网络 | 不需要。测试全程走 FastAPI TestClient，不起端口、不连外网 |
| 环境变量 | 不需要。凭证类配置一律不落地；两个演示开关（含两道闸）见第六节 |

安装与自检（逐条命令 + 预期输出）：

```bash
python -m venv .venv
.venv/Scripts/activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
# 预期：Successfully installed fastapi-0.136.1 httpx-0.28.1 pydantic-2.14.4 pytest-9.2.0

python -m scripts.check_registry
# 预期：逐行打印 11 个前缀各自的接口数，末行 registry_ok=true

python -m pytest tests/ -q
# 预期末行：183 passed

python -m scripts.build_report
# 预期：templates=28 endpoints=29 rows=58 leaks=0 allowlisted=9

python -m scripts.capture_checks
# 预期：重采集 docs/checks/ 下 6 份日志，末行 pytest_exit=0 report_exit=0
```

## 二、这套扫描器怎么工作

```
app/            接口桩：11 个路由前缀，全部返回虚构数据（可整体替换成客户实现）
  routes/       每个前缀一个 APIRouter
  redact.py     接口桩侧的出参脱敏（自由文本里的联系方式样例替换为固定遮蔽串）
  identity.py   身份解析：会员 / 员工（对接点是换掉这个函数）
  demo_hooks.py 演示开关：只用环境变量触发，含两道闸（显式放行 + 非 CI），用于 AC1 / AC2 的日志取证
scan/           扫描器
  enumerate.py  从 app.routes 反射枚举 11 个前缀下的全部路由模板
  registry.py   显式登记表：路由模板 -> 用例标识
  leak_check.py 键名黑名单 + 值正则 + 掩码 + 白名单 + 递归限制
  whitelist.py  数字串白名单（票号等必须返回的号码）
  report.py     生成 reports/report.md（接口 × 身份 全量矩阵）
tests/          183 条用例，八个测试文件
fixtures/       虚构植入数据集
.github/workflows/leak-scan.yml   CI 门禁
docs/checks/    四类运行日志（AC1–AC4 各一份）
```

三个关键设计：

1. **接口清单不手写**。`scan/enumerate.py` 直接反射 `app.routes`，按路径段匹配 11 个前缀，
   与 `scan/registry.py` 求差集；差集非空即报 `UNDECLARED_ENDPOINT: <path>` 并让测试失败。
   新增接口而忘记登记，CI 立刻红。
2. **判定不认「掩码」**。完整手机号、带区号座机、邮箱、`wxid_` 前缀之外，
   `138****8000`、`****8000`、`138****` 三种部分掩码同样判为不合格。
3. **数字串必须显式登记**。8 位以上纯数字（票号、工单号、导出凭据号）不靠「整条规则关掉」，
   而是在 `scan/whitelist.py` 里按「路由模板 + 字段路径后缀 + 正则 + 原因」逐条登记，
   报告里单列一节列出放行了什么、为什么放行。

## 三、逐条验收标准的复现步骤

### AC1 人为新增一个未登记用例的接口时测试失败

```bash
# PowerShell
$env:LEAK_DEMO_ALLOW = "1"                                     # 闸一：显式放行
$env:LEAK_DEMO_EXTRA_ROUTE = "/api/mini/events/__leak_probe"
python -m scripts.check_registry          # 退出码 1，末行 UNDECLARED_ENDPOINT: /api/mini/events/__leak_probe
python -m pytest tests/test_api_surface.py::test_every_template_is_registered -q   # 1 failed
Remove-Item Env:LEAK_DEMO_EXTRA_ROUTE; Remove-Item Env:LEAK_DEMO_ALLOW   # 恢复基线
python -m pytest tests/test_api_surface.py::test_every_template_is_registered -q   # 1 passed
```

应看到：注入后路由模板总数从 28 变 29，错误信息逐字包含新接口路径；移除变量后同一命令转绿。
证据文件：`docs/checks/ac1-unguarded-route.log`（三段输出 + 三个退出码）。

清空环境变量即恢复基线——演示开关不是测试替身，CI 里不设这两个变量。

### AC2 人为让任一接口返回虚构手机号时测试失败，并输出接口路径与字段路径

```bash
$env:LEAK_DEMO_ALLOW = "1"                                     # 闸一：显式放行
$env:LEAK_DEMO_LEAK = "/api/mini/support/tickets"
python -m pytest "tests/test_api_surface.py::test_endpoint_has_no_contact_leak[GET-/api/mini/support/tickets-member]" -q
# 预期 1 failed，失败文本形如：
#   LEAK_DETECTED route=/api/mini/support/tickets hits=3
#     key_phone: path=/api/mini/support/tickets field=data.items[0].contact_phone value='13800138000'
#     value_phone: path=/api/mini/support/tickets field=data.items[0].contact_phone value='13800138000'
#     value_numeric_run: path=/api/mini/support/tickets field=data.items[0].contact_phone value='13800138000'
python -m scripts.build_report            # 该接口两行在报告里记为 LEAK
Remove-Item Env:LEAK_DEMO_LEAK; Remove-Item Env:LEAK_DEMO_ALLOW
```

应看到：`path=` 后面是接口路径，`field=` 后面是精确到 JSON 层级的字段路径（`data.items[0].contact_phone`）；
同一字段同时命中键名规则与值规则时逐条列出，不合并成一条。
证据文件：`docs/checks/ac2-leak-detected.log`。

### AC3 报告中每个接口都有会员身份与员工身份两行结果

```bash
python -m scripts.build_report
# 预期：templates=28 endpoints=29 rows=58 leaks=0 allowlisted=9
```

`reports/report.md` 的结果表列：接口 / 方法 / 身份 / 结果 / 命中字段路径。
「接口」按 (方法, 路由模板) 计——`/api/mini/signups` 上的 GET 与 POST 是两个接口，各自两行。
身份受限的接口（例如 `/api/mini/me/profile` 只有会员能看）**照样保留两行**，
员工那一行写 `NOT_ALLOWED`，不省略，否则行数算术就没有意义。

应看到：29 个接口 × 2 身份 = 58 行；逐接口核对，29 个接口全部 `member,staff` 各一行（每行末尾标 OK）。
证据文件：`docs/checks/ac3-report-shape.log`（行数统计 + 29 个接口的逐条核对结果）。

### AC4 CI 配置中该测试失败会阻断合并

`.github/workflows/leak-scan.yml` 全文：

```yaml
name: leak-scan

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  leak-scan:
    name: leak-scan
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Enumerate routes and compare with registry
        run: python -m scripts.check_registry
      - name: Contact leak scan (pytest)
        run: python -m pytest tests/ -q
      - name: Upload report and logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: leak-scan-report
          path: |
            reports/report.md
            docs/checks/
```

要点：

- `pull_request` 触发 —— 合并前就跑到；
- `python -m pytest tests/ -q` 非 0 退出即 step 失败，进而 job 失败；
- **全文没有 `continue-on-error`**（有用例守着这一条：`tests/test_ci_config.py`）；
- 没有任何 `|| true` / `; true` 把退出码抹平。

阻断合并的最后一环是仓库设置里的分支保护（required status checks 勾选 `leak-scan`）。
这一步**不在 yml 里，需要仓库管理员在 Settings → Branches 配一次**：

1. Settings → Branches → Add branch protection rule，分支填 `main`；
2. 勾选 Require a pull request before merging；
3. 勾选 Require status checks to pass before merging，搜索并选中 `leak-scan`；
4. 保存。此后该检查不通过，PR 的合并按钮为禁用状态。

本仓库交付的是可用的工作流文件本身；分支保护属于仓库设置，本文如实说明它需要单独配置，
不声称已经开启。

证据文件：`docs/checks/ac4-ci-blocking.log`（工作流全文、三条 grep 计数、本地按 CI 同序列复跑的退出码红/绿两段）。

## 四、判定口径（改口径先改测试）

| 维度 | 规则 |
| --- | --- |
| 键名黑名单 | `phone` `mobile` `tel` `email` `wechat` `wx_id` `qq` `contact`，不区分大小写、含嵌套层 |
| 值正则 | 手机 `1[3-9]` + 9 位数字；座机 `0` + 2~3 位区号 + 7~8 位号码；邮箱；`wxid_` 前缀 |
| 掩码 | 前三后四、只留后四位、只留前三位，三种形态都判不合格 |
| 长数字串 | 8 位以上纯数字另计一条，须在白名单显式登记 |
| 递归 | 深度上限 8 层；栈内 `id()` 去环，自引用不爆栈，超限与环路各记一条命中 |

正则带数字边界：16 位票号中间那段「0 + 区号 + 号码」不会因为长得像座机而被判泄露，
票号是否放行完全由白名单决定，而不是靠关掉规则。

## 五、白名单（必须返回的数字串）

`scan/whitelist.py` 里 5 条规则，每条都写明是哪个接口的哪个字段、为什么可以放行：

| 路由模板 | 字段 | 正则 | 原因 |
| --- | --- | --- | --- |
| `/api/mini/tickets` | `ticket_no` | 16 位纯数字 | 电子票票号，签发时生成，不含手机号片段 |
| `/api/mini/tickets/{ticket_key}` | `ticket_no` | 16 位纯数字 | 电子票票号（详情接口同源同格式） |
| `/api/mini/support/tickets` | `ticket_id` | st- 加 4 位序号 | 客服工单号 |
| `/api/mini/privacy/export` | `export_id` | exp- 加日期加 4 位序号 | 个人信息导出凭据编号 |
| `/api/mini/privacy/deletion` | `request_id` | del- 加日期加 4 位序号 | 注销申请单号 |

粒度到「路由模板 + 字段路径后缀 + 完整匹配」：同名数字串换个字段或换个接口就不再享有豁免，
所以 `ticket_no` 里若真塞了 11 位手机号，照样被抓（`tests/test_leak_check.py` 有用例守着）。

## 六、演示开关（AC1 / AC2 取证用）

| 环境变量 | 作用 | 默认 |
| --- | --- | --- |
| `LEAK_DEMO_ALLOW` | 闸一：必须逐字为 `1`，否则下面两个变量一律不生效 | 空（关闭） |
| `LEAK_DEMO_EXTRA_ROUTE` | 往 app 里再挂一条未登记路由，演示漏登记会让测试变红 | 空（不挂） |
| `LEAK_DEMO_LEAK` | 让该路由返回带虚构手机号的响应，演示泄露会让测试变红 | 空（不注入） |

闸二：`CI` 为 `1` / `true` / `yes` 时一律拒绝激活，哪怕前两个变量都设了。所以这套开关带不进 CI，CI 上恒为真实基线。

`app/demo_hooks.py` 的 `demo_enabled()` 是这两道闸的唯一实现，`tests/test_demo_hooks.py` 的 10 条用例守着它（默认关、单设等不生效、两闸齐开才生效、CI 一律拒、放行值必须逐字为 1、默认 app 路由表里没有探针路由）。

## 七、测试分布

| 文件 | 覆盖 |
| --- | --- |
| `tests/test_api_surface.py` | 接口 × 身份全矩阵扫描、前缀覆盖、登记比对 |
| `tests/test_registry_guard.py` | AC1：未登记接口检出、错误文本逐字断言、登记后转绿、下线接口只告警 |
| `tests/test_ac2_injection.py` | AC2：注入手机号 / 掩码 / 邮箱 / wxid / 座机五类，断言路径精确 |
| `tests/test_leak_check.py` | 扫描器自身：键名、值正则、掩码、白名单、递归深度、循环引用 |
| `tests/test_report_shape.py` | AC3：行数算术、双身份、受限接口不省略、四列结构 |
| `tests/test_ci_config.py` | AC4：yml 断言 PR 触发、跑 pytest、无 continue-on-error |
| `tests/test_identity_and_routes.py` | 身份矩阵、未知身份 400、脱敏后正文 |
| `tests/test_demo_hooks.py` | 演示开关两道闸：默认关、CI 拒绝、放行值逐字匹配 |

实测：**183 passed**

## 八、对接点（换成客户自己的实现）

本仓库的 `app/` 是接口桩，扫描器与测试不依赖桩的内部实现，替换步骤：

1. 把 `app/routes/*` 换成客户真实路由，保持 11 个前缀与响应外壳 `{"data": ...}` 不变；
2. 把 `app/identity.py` 的 `identity_from_header` 换成解析微信登录态 / 员工令牌的实现，
   返回 `"member"` 或 `"staff"`；
3. `scan/registry.py` 按新路由表补齐登记（漏登记会直接由 CI 报出来）；
4. `scan/whitelist.py` 补登记客户侧必须返回的数字串；
5. `python -m pytest tests/ -q` 跑到全绿即接入完成。

依赖其它工单的接口一律用桩：本仓库不含任何真实数据库连接、缓存连接或第三方 SDK。

## 九、产物索引

| 路径 | 内容 |
| --- | --- |
| `reports/report.md` | 报告样例：58 行接口 × 身份矩阵 + 白名单小节 |
| `docs/checks/ac1-unguarded-route.log` | AC1 日志（注入后 / 恢复后三段） |
| `docs/checks/ac2-leak-detected.log` | AC2 日志（含 `path=` 与 `field=` 原文） |
| `docs/checks/ac3-report-shape.log` | AC3 日志（行数统计 + 逐接口双身份核对） |
| `docs/checks/ac4-ci-blocking.log` | AC4 日志（yml 关键行 + 本地退出码红绿） |
| `docs/checks/pytest-full.log` | 全量测试输出 |


