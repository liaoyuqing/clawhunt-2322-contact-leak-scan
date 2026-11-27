"""扫描器自身单测：键名黑名单 / 4 类值正则 / 掩码 / 白名单 / 递归限制 / 去环。

这些用例不碰 FastAPI，只验判定口径本身，改口径时先在这里红。
"""
from __future__ import annotations

import pytest

from scan.leak_check import (
    KEY_BLACKLIST,
    MAX_DEPTH,
    key_is_blacklisted,
    scan_payload,
    scan_text,
    value_kind,
    value_kinds,
)
from scan import whitelist


@pytest.mark.parametrize("key", KEY_BLACKLIST)
def test_each_blacklisted_key_is_caught(key):
    assert key_is_blacklisted(key) is not None


@pytest.mark.parametrize(
    "key",
    ["contact_phone", "phoneNumber", "memberMobile", "staff_email", "wechat_id", "wxId", "ownerTel", "QQ"],
)
def test_compound_keys_are_caught(key):
    assert key_is_blacklisted(key) is not None, f"{key} 是复合键，应命中黑名单"


@pytest.mark.parametrize("key", ["hotel_name", "ticket_no", "telephone_booth", "summary", "public_contactless"])
def test_non_contacting_keys_are_not_caught(key):
    assert key_is_blacklisted(key) is None


def test_key_blacklist_is_case_insensitive():
    assert key_is_blacklisted("PHONE") == "phone"
    assert key_is_blacklisted("Email") == "email"


@pytest.mark.parametrize(
    "value,kind",
    [
        ("13800001111", "value_phone"),
        ("021-12345678", "value_landline"),
        ("member.one@example.com", "value_email"),
        ("wxid_abc123", "value_wxid"),
        ("138****1111", "value_masked_phone"),
        ("****1111", "value_masked_tail"),
        ("138****", "value_masked_head"),
    ],
    ids=["phone", "landline", "email", "wxid", "masked", "tail", "head"],
)
def test_value_rules_hit(value, kind):
    assert value_kind(value) == kind


@pytest.mark.parametrize(
    "value",
    ["st-1001", "evt-1001", "会员甲", "2026-12-05T09:30:00+08:00", "A-12"],
)
def test_value_rules_do_not_misfire(value):
    assert value_kind(value) is None, f"{value} 不应被判为联系方式"


def test_eleven_digits_outside_phone_ranges_is_not_a_phone():
    """11 位但不在 1[3-9] 号段：不判手机号；它仍落进长数字串规则，去留由白名单决定。"""
    kinds = value_kinds("12345678901")
    assert "value_phone" not in kinds
    assert "value_numeric_run" in kinds


def test_long_numeric_run_is_flagged_even_if_not_a_phone():
    """8 位以上纯数字：不一定是手机号，但必须显式登记，否则视为可疑（票号走这条）。"""
    assert value_kind("2026112700001234") == "value_numeric_run"
    assert value_kind("12345678") == "value_numeric_run"
    assert value_kind("1234567") is None


def test_value_kinds_collects_all_matches_in_one_string():
    text = "电话 13800001111，邮箱 a@b.com，微信 wxid_abc123"
    kinds = set(value_kinds(text))
    assert {"value_phone", "value_email", "value_wxid"} <= kinds


def test_nested_list_reports_json_path():
    payload = {"data": {"items": [{"ticket_id": "st-1001", "contact_phone": "13800001111"}]}}
    result = scan_payload(payload, route="/api/mini/support/tickets")
    paths = [hit.field_path for hit in result.hits]
    assert "data.items[0].contact_phone" in paths


def test_deep_nesting_third_level_is_reported():
    payload = {"data": {"items": [{"member": {"profile": {"mobile": "13900002222"}}}]}}
    result = scan_payload(payload, route="/api/mini/me/profile")
    assert any(hit.field_path == "data.items[0].member.profile.mobile" for hit in result.hits)


def test_free_text_values_are_scanned():
    result = scan_text("现场联系人 13800001111，邮箱 a@b.com，微信 wxid_abc123。")
    kinds = {hit.kind for hit in result.hits}
    assert {"value_phone", "value_email", "value_wxid"} <= kinds


def test_clean_payload_has_no_hits():
    payload = {"data": {"items": [{"event_id": "evt-1001", "title": "秋季资源对接会（虚构）"}], "total": 1}}
    result = scan_payload(payload, route="/api/mini/events")
    assert result.ok and result.hits == []


def test_depth_limit_stops_recursion():
    node: dict = {}
    cursor = node
    for _ in range(MAX_DEPTH + 5):
        cursor["next"] = {}
        cursor = cursor["next"]
    cursor["mobile"] = "13800001111"
    result = scan_payload({"data": node}, route="/api/mini/events")
    assert any(hit.kind == "depth_limit_exceeded" for hit in result.hits)


def test_circular_reference_does_not_blow_the_stack():
    node: dict = {"mobile": "13800001111"}
    node["self"] = node
    result = scan_payload({"data": node}, route="/api/mini/events")
    kinds = [hit.kind for hit in result.hits]
    assert "circular_reference" in kinds


def test_list_cycle_is_detected_too():
    items: list = []
    items.append(items)
    result = scan_payload({"data": {"items": items}}, route="/api/mini/events")
    assert any(hit.kind == "circular_reference" for hit in result.hits)


def test_whitelisted_ticket_number_is_not_a_hit():
    payload = {"data": {"items": [{"ticket_no": "2026112700001234"}]}}
    result = scan_payload(payload, route="/api/mini/tickets")
    assert result.ok
    assert len(result.allowed) == 1
    assert result.allowed[0].field_path == "data.items[0].ticket_no"


def test_whitelist_is_scoped_to_its_route():
    payload = {"data": {"items": [{"ticket_no": "2026112700001234"}]}}
    result = scan_payload(payload, route="/api/mini/events")
    assert not result.ok, "同一字段名换了路由就不再享有白名单"


def test_whitelist_is_scoped_to_its_field():
    payload = {"data": {"items": [{"other_no": "2026112700001234"}]}}
    result = scan_payload(payload, route="/api/mini/tickets")
    assert not result.ok, "白名单只认 ticket_no 字段，不认同路由的其它数字串"


def test_whitelist_requires_full_match():
    payload = {"data": {"items": [{"ticket_no": "20261127000012345"}]}}
    result = scan_payload(payload, route="/api/mini/tickets")
    assert not result.ok, "17 位数字不该被 16 位票号规则放过"


def test_whitelist_never_swallows_a_phone_number():
    payload = {"data": {"items": [{"ticket_no": "13800001111"}]}}
    result = scan_payload(payload, route="/api/mini/tickets")
    assert result.ok is False


def test_whitelist_descriptions_are_not_empty():
    rules = whitelist.describe()
    assert len(rules) == 5
    assert all(rule["reason"] for rule in rules)
