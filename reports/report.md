# 联系方式泄露扫描报告（虚构数据）

生成方式：`python -m scripts.build_report`。本文件由脚本产出，不要手改。

口径说明：接口 =（方法, 路由模板），同一模板上的 GET 与 POST 各自算一个接口，
每个接口必须有 member 与 staff 两行。

## 汇总

| 指标 | 数值 |
| --- | --- |
| 路由模板数 | 28 |
| 接口数（方法 + 路径） | 29 |
| 身份数 | 2 |
| 报告行数 | 58 |
| 期望行数（接口数 × 2） | 58 |
| 泄露行数 | 0 |
| 白名单放行条目数 | 9 |

## 逐接口 × 身份结果

列含义：接口 = FastAPI 路由模板；身份 = member / staff；结果 = PASS / LEAK / NOT_ALLOWED / EMPTY_BODY；命中字段路径 = JSON 路径，PASS 时为 -。

| 接口 | 方法 | 身份 | 结果 | 命中字段路径 |
| --- | --- | --- | --- | --- |
| `/api/mini/butler/tasks` | GET | member | PASS | `-` |
| `/api/mini/butler/tasks` | GET | staff | PASS | `-` |
| `/api/mini/butler/tasks/{task_id}` | GET | member | PASS | `-` |
| `/api/mini/butler/tasks/{task_id}` | GET | staff | PASS | `-` |
| `/api/mini/events` | GET | member | PASS | `-` |
| `/api/mini/events` | GET | staff | PASS | `-` |
| `/api/mini/events/{event_id}` | GET | member | PASS | `-` |
| `/api/mini/events/{event_id}` | GET | staff | PASS | `-` |
| `/api/mini/events/{event_id}/agenda` | GET | member | PASS | `-` |
| `/api/mini/events/{event_id}/agenda` | GET | staff | PASS | `-` |
| `/api/mini/faq` | GET | member | PASS | `-` |
| `/api/mini/faq` | GET | staff | PASS | `-` |
| `/api/mini/faq/{faq_id}` | GET | member | PASS | `-` |
| `/api/mini/faq/{faq_id}` | GET | staff | PASS | `-` |
| `/api/mini/me/profile` | GET | member | PASS | `-` |
| `/api/mini/me/profile` | GET | staff | NOT_ALLOWED | `-` |
| `/api/mini/me/questionnaires` | GET | member | PASS | `-` |
| `/api/mini/me/questionnaires` | GET | staff | PASS | `-` |
| `/api/mini/me/questionnaires/{questionnaire_id}` | GET | member | PASS | `-` |
| `/api/mini/me/questionnaires/{questionnaire_id}` | GET | staff | PASS | `-` |
| `/api/mini/posts` | GET | member | PASS | `-` |
| `/api/mini/posts` | GET | staff | PASS | `-` |
| `/api/mini/posts/{post_id}` | GET | member | PASS | `-` |
| `/api/mini/posts/{post_id}` | GET | staff | PASS | `-` |
| `/api/mini/privacy/deletion` | POST | member | PASS | `-` |
| `/api/mini/privacy/deletion` | POST | staff | NOT_ALLOWED | `-` |
| `/api/mini/privacy/export` | GET | member | PASS | `-` |
| `/api/mini/privacy/export` | GET | staff | PASS | `-` |
| `/api/mini/privacy/policy` | GET | member | PASS | `-` |
| `/api/mini/privacy/policy` | GET | staff | PASS | `-` |
| `/api/mini/signups` | GET | member | PASS | `-` |
| `/api/mini/signups` | GET | staff | PASS | `-` |
| `/api/mini/signups` | POST | member | PASS | `-` |
| `/api/mini/signups` | POST | staff | PASS | `-` |
| `/api/mini/signups/{signup_id}` | GET | member | PASS | `-` |
| `/api/mini/signups/{signup_id}` | GET | staff | PASS | `-` |
| `/api/mini/staff/cases` | GET | member | NOT_ALLOWED | `-` |
| `/api/mini/staff/cases` | GET | staff | PASS | `-` |
| `/api/mini/staff/profile` | GET | member | NOT_ALLOWED | `-` |
| `/api/mini/staff/profile` | GET | staff | PASS | `-` |
| `/api/mini/staff/shifts` | GET | member | NOT_ALLOWED | `-` |
| `/api/mini/staff/shifts` | GET | staff | PASS | `-` |
| `/api/mini/subscriptions` | GET | member | PASS | `-` |
| `/api/mini/subscriptions` | GET | staff | PASS | `-` |
| `/api/mini/subscriptions/{template_id}/toggle` | POST | member | PASS | `-` |
| `/api/mini/subscriptions/{template_id}/toggle` | POST | staff | PASS | `-` |
| `/api/mini/support/cases` | GET | member | PASS | `-` |
| `/api/mini/support/cases` | GET | staff | PASS | `-` |
| `/api/mini/support/cases/{case_id}` | GET | member | PASS | `-` |
| `/api/mini/support/cases/{case_id}` | GET | staff | PASS | `-` |
| `/api/mini/support/handoff` | POST | member | PASS | `-` |
| `/api/mini/support/handoff` | POST | staff | PASS | `-` |
| `/api/mini/support/tickets` | GET | member | PASS | `-` |
| `/api/mini/support/tickets` | GET | staff | PASS | `-` |
| `/api/mini/tickets` | GET | member | PASS | `-` |
| `/api/mini/tickets` | GET | staff | PASS | `-` |
| `/api/mini/tickets/{ticket_key}` | GET | member | PASS | `-` |
| `/api/mini/tickets/{ticket_key}` | GET | staff | PASS | `-` |

## 数字串白名单（显式登记，放行原因逐条列出）

| 路由模板 | 字段路径后缀 | 正则 | 放行原因 |
| --- | --- | --- | --- |
| `/api/mini/tickets` | `ticket_no` | `\d{16}` | 电子票票号：16 位纯数字，签发时生成，不含任何手机号片段 |
| `/api/mini/tickets/{ticket_key}` | `ticket_no` | `\d{16}` | 电子票票号（详情接口同源同格式） |
| `/api/mini/support/tickets` | `ticket_id` | `st-\d{4}` | 客服工单号：st- 前缀 + 4 位序号，非手机号 |
| `/api/mini/privacy/export` | `export_id` | `exp-\d{8}-\d{4}` | 个人信息导出凭据编号：exp- 前缀 + 日期 + 4 位序号，纯业务标识 |
| `/api/mini/privacy/deletion` | `request_id` | `del-\d{8}-\d{4}` | 注销申请单号：del- 前缀 + 日期 + 4 位序号，纯业务标识 |

### 本次运行实际命中白名单的字段

| 路由模板 | 字段路径 | 值 | 原因 |
| --- | --- | --- | --- |
| `/api/mini/privacy/deletion` | `data.request_id` | `del-20261127-0001` | 注销申请单号：del- 前缀 + 日期 + 4 位序号，纯业务标识 |
| `/api/mini/privacy/export` | `data.export_id` | `exp-20261127-0001` | 个人信息导出凭据编号：exp- 前缀 + 日期 + 4 位序号，纯业务标识 |
| `/api/mini/privacy/export` | `data.export_id` | `exp-20261127-0001` | 个人信息导出凭据编号：exp- 前缀 + 日期 + 4 位序号，纯业务标识 |
| `/api/mini/tickets` | `data.items[0].ticket_no` | `2026112700001234` | 电子票票号：16 位纯数字，签发时生成，不含任何手机号片段 |
| `/api/mini/tickets` | `data.items[1].ticket_no` | `2026112700005678` | 电子票票号：16 位纯数字，签发时生成，不含任何手机号片段 |
| `/api/mini/tickets` | `data.items[0].ticket_no` | `2026112700001234` | 电子票票号：16 位纯数字，签发时生成，不含任何手机号片段 |
| `/api/mini/tickets` | `data.items[1].ticket_no` | `2026112700005678` | 电子票票号：16 位纯数字，签发时生成，不含任何手机号片段 |
| `/api/mini/tickets/{ticket_key}` | `data.ticket_no` | `2026112700001234` | 电子票票号（详情接口同源同格式） |
| `/api/mini/tickets/{ticket_key}` | `data.ticket_no` | `2026112700001234` | 电子票票号（详情接口同源同格式） |

## 判定口径

- 键名黑名单（不区分大小写、含嵌套层）：phone / mobile / tel / email / wechat / wx_id / qq / contact。
- 值正则：11 位大陆手机号 `1[3-9]\d{9}`；带区号座机 `0\d{2,3}-?\d{7,8}`；邮箱；`wxid_` 前缀。
- 掩码判不合格：前三后四 `1[3-9]\d\*{2,}\d{4}`、只留后四位 `\*{3,}\d{4}`、只留前三位 `1[3-9]\d\*{3,}`。
- 递归限制：深度上限 8 层，栈内 id() 去环；超限与环路本身记一条命中（该段视为未扫描）。
