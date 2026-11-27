"""pytest 公共夹具与路径。"""
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


@pytest.fixture
def fixture_dir():
    return FIXTURE_DIR


def read_fixture(platform: str, name: str) -> bytes:
    return (FIXTURE_DIR / platform / name).read_bytes()
