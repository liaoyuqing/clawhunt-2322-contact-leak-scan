from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import injection  # noqa: E402  (必须在 sys.path 调整之后)
from app.main import create_app  # noqa: E402


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_overrides():
    """每个用例开始与结束都清空故障注入表，避免用例之间互相污染。"""
    injection.clear()
    yield
    injection.clear()


@pytest.fixture()
def identity_headers():
    def build(identity: str) -> dict[str, str]:
        return {"X-Mini-Identity": identity}

    return build
