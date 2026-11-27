"""接口桩的身份切换：会员 / 员工。

真实系统里身份来自微信登录态与员工后台 token；本单只交付回归测试与 CI，
所以接口桩用请求头 X-Mini-Identity 显式声明身份，README 写明这是对接点。
对接点：把 identity_from_header 换成解析登录态（JWT / session）即可。
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

MEMBER = "member"
STAFF = "staff"
IDENTITIES = (MEMBER, STAFF)


def identity_from_header(x_mini_identity: str = Header(default=MEMBER)) -> str:
    value = (x_mini_identity or MEMBER).strip().lower()
    if value not in IDENTITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "unknown_identity", "accepted": list(IDENTITIES)},
        )
    return value


def require(*allowed: str):
    """依赖工厂：只允许列出的身份访问，其余返回 403（并在响应体里给出原因）。"""
    allowed_set = tuple(allowed)

    def _guard(identity: str = Header(..., alias="X-Mini-Identity")) -> str:
        value = identity_from_header(identity)
        if value not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "identity_not_allowed", "identity": value, "allowed": list(allowed_set)},
            )
        return value

    return _guard
