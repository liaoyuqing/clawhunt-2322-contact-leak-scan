r"""联系方式泄露判定：键名黑名单 + 值正则 + 掩码 + 白名单豁免。

判定顺序（对每个节点）：
1. 键名候选：dict 的每个键（含嵌套层）先过 key_is_blacklisted；
2. 字符串值：依次过 手机 / 座机 / 邮箱 / wxid / 掩码 五组正则，命中几条记几条；
3. 另有「长数字串」规则（8 位以上纯数字）：不一定是手机号，但必须显式登记，
   否则视为可疑——票号即走这条路径，靠 scan/whitelist.py 逐字段豁免；
4. 命中先问白名单（路由模板 + 字段路径后缀 + 完整匹配），放过的条目单独收集，
   报告里单列一节；未豁免的记成 Hit，字段路径精确到 JSON 层级，例如
   data.items[0].contact_phone。

正则一律用数字/单词边界（(?<!\d)...(?!\d)）：16 位票号中间那段「0 + 区号 + 号码」
长得像座机，加边界后不会被当成座机；票号是否放行完全由白名单决定，
而不是靠关掉规则。

递归安全：深度上限 MAX_DEPTH（默认 8 层）+ 栈内 id() 去环，
dict/list 自引用不会爆栈，超限与环路各自记一条 Hit（该段视为未扫到）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from scan import whitelist

MAX_DEPTH = 8

# 键名黑名单（不区分大小写，含嵌套层）。
KEY_BLACKLIST = ("phone", "mobile", "tel", "email", "wechat", "wx_id", "qq", "contact")

# 长词（>= 4 字符）允许出现在复合键的任意位置（contact_phone / phoneNumber / telephone）；
# 短词（tel / qq）只认独立单词，避免 hotel 这类正常单词被误伤。
LONG_WORDS = ("phone", "mobile", "email", "wechat", "contact")
SHORT_WORDS = ("tel", "qq")

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NON_ALNUM = re.compile(r"[^0-9a-zA-Z]+")

VALUE_RULES = (
    ("value_phone", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("value_landline", re.compile(r"(?<!\d)0\d{2,3}-?\d{7,8}(?!\d)")),
    ("value_email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("value_wxid", re.compile(r"wxid_[0-9a-zA-Z]+")),
    ("value_masked_phone", re.compile(r"(?<!\d)1[3-9]\d\*{2,}\d{4}(?!\d)")),
    ("value_masked_tail", re.compile(r"\*{3,}\d{4}(?!\d)")),
    ("value_masked_head", re.compile(r"(?<!\d)1[3-9]\d\*{3,}")),
    ("value_numeric_run", re.compile(r"(?<!\d)\d{8,}(?!\d)")),
)


@dataclass
class Hit:
    route: str
    field_path: str
    kind: str
    value: str

    def as_dict(self) -> dict:
        return {"route": self.route, "field_path": self.field_path, "kind": self.kind, "value": self.value}

    def __str__(self) -> str:
        return f"{self.kind}: path={self.route} field={self.field_path} value={self.value!r}"


@dataclass
class AllowHit:
    route: str
    field_path: str
    value: str
    reason: str


@dataclass
class ScanResult:
    route: str
    hits: list[Hit] = field(default_factory=list)
    allowed: list[AllowHit] = field(default_factory=list)
    scanned_nodes: int = 0

    @property
    def ok(self) -> bool:
        return not self.hits

    def raise_for_leak(self) -> None:
        if self.hits:
            lines = ["LEAK_DETECTED route=%s hits=%d" % (self.route, len(self.hits))]
            lines.extend("  " + str(hit) for hit in self.hits)
            raise AssertionError("\n".join(lines))


def key_tokens(key: str) -> list[str]:
    spaced = _CAMEL.sub(" ", key)
    return [token for token in _NON_ALNUM.split(spaced.lower()) if token]


def key_is_blacklisted(key: str) -> str | None:
    """命中则返回命中的黑名单词，未命中返回 None。"""
    tokens = key_tokens(key)
    joined = "".join(tokens)
    for word in SHORT_WORDS:
        if word in tokens:
            return word
    if "wxid" in tokens or (tokens[:1] == ["wx"] and "id" in tokens):
        return "wx_id"
    for word in LONG_WORDS:
        if word in tokens:
            return word
    return None


def value_kinds(value: str) -> list[str]:
    """一条字符串里可能同时有手机号 + 邮箱 + 微信号，逐条收集，不取首个。"""
    return [kind for kind, pattern in VALUE_RULES if pattern.search(value)]


def value_kind(value: str) -> str | None:
    kinds = value_kinds(value)
    return kinds[0] if kinds else None


def _join(parent: str, key: str) -> str:
    return f"{parent}.{key}" if parent else key


def scan_payload(payload, route: str, max_depth: int = MAX_DEPTH) -> ScanResult:
    result = ScanResult(route=route)
    stack: set[int] = set()

    def record(path: str, kind: str, value: str) -> None:
        rule = whitelist.allowlisted(route, path, value)
        if rule is not None:
            result.allowed.append(AllowHit(route, path, value, rule.reason))
            return
        result.hits.append(Hit(route, path, kind, value))

    def walk(node, path: str, depth: int) -> None:
        if depth > max_depth:
            result.hits.append(Hit(route, path, "depth_limit_exceeded", f"max_depth={max_depth}"))
            return
        if isinstance(node, (dict, list, tuple)):
            marker = id(node)
            if marker in stack:
                result.hits.append(Hit(route, path, "circular_reference", "self_referencing_container"))
                return
            stack.add(marker)
            try:
                if isinstance(node, dict):
                    for key, child in node.items():
                        child_path = _join(path, str(key))
                        result.scanned_nodes += 1
                        word = key_is_blacklisted(str(key))
                        if word is not None:
                            record(child_path, "key_" + word, str(child))
                        walk(child, child_path, depth + 1)
                else:
                    for index, child in enumerate(node):
                        walk(child, f"{path}[{index}]", depth + 1)
            finally:
                stack.discard(marker)
            return
        if isinstance(node, str):
            result.scanned_nodes += 1
            for kind in value_kinds(node):
                record(path, kind, node)
            return
        result.scanned_nodes += 1

    walk(payload, "", 0)
    return result


def scan_text(text: str, route: str = "<text>") -> ScanResult:
    """扫自由文本（例如 README / 日志），用于仓库自查。"""
    return scan_payload({"text": text}, route)
