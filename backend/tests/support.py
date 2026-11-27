"""测试共用的样例账单路径。"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

ALIPAY_CSV = FIXTURES / "alipay_sample.csv"
WECHAT_CSV = FIXTURES / "wechat_sample.csv"
BROKEN_CSV = FIXTURES / "broken_rows.csv"
