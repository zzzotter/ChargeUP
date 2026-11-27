"""快捷录入/交易列表契约测试（Pydantic v2）。"""
import pytest
from pydantic import ValidationError

from src.ledger_guard.contracts import (
    Direction,
    PagedResponse,
    QuickEntryCreate,
    Source,
    TransactionOut,
    mock_data,
)


def test_mock_transactions_match_contract():
    items = [TransactionOut(**row) for row in mock_data.MOCK_TRANSACTIONS]
    assert len(items) == len(mock_data.MOCK_TRANSACTIONS)
    page = PagedResponse[TransactionOut](**mock_data.MOCK_PAGE)
    assert page.total == len(items)
    assert page.page == 1 and page.page_size == 20


def test_valid_quick_entry():
    entry = QuickEntryCreate(**mock_data.MOCK_QUICK_ENTRY)
    assert entry.source == Source.WECHAT
    assert isinstance(entry.amount_cents, int)
    assert entry.amount_cents == 1234
    assert entry.direction == Direction.EXPENSE


def test_amount_must_be_positive_int():
    bad = dict(mock_data.MOCK_QUICK_ENTRY)
    bad["amount_cents"] = 0
    with pytest.raises(ValidationError):
        QuickEntryCreate(**bad)
    bad["amount_cents"] = -100
    with pytest.raises(ValidationError):
        QuickEntryCreate(**bad)


def test_float_amount_rejected():
    bad = dict(mock_data.MOCK_QUICK_ENTRY)
    bad["amount_cents"] = 12.34
    with pytest.raises(ValidationError):
        QuickEntryCreate(**bad)


def test_invalid_enum_and_missing_field_rejected():
    bad = dict(mock_data.MOCK_QUICK_ENTRY)
    bad["source"] = "UNKNOWN"
    with pytest.raises(ValidationError):
        QuickEntryCreate(**bad)

    bad = dict(mock_data.MOCK_QUICK_ENTRY)
    del bad["item_name"]
    with pytest.raises(ValidationError):
        QuickEntryCreate(**bad)


def test_undeclared_field_forbidden():
    bad = dict(mock_data.MOCK_QUICK_ENTRY)
    bad["unexpected"] = "x"
    with pytest.raises(ValidationError):
        QuickEntryCreate(**bad)
