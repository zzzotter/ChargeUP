"""第 7 天：自定义规则优先级与未匹配归箱。"""
from src.ledger_guard.domain import (
    CategoryRule,
    RuleField,
    RuleSource,
    apply_classification,
    match_category,
)
from src.ledger_guard.parser.models import Direction

from .helpers import make_tx


def test_keyword_match_on_item_name():
    tx = make_tx("t1", 3500, Direction.EXPENSE, item_name="拿铁咖啡")
    rule = CategoryRule(1, category_id=10, keyword="咖啡")
    assert match_category(tx, [rule]) == 10


def test_keyword_match_on_counterparty():
    tx = make_tx("t2", 2880, Direction.EXPENSE, item_name="车费", counterparty="滴滴出行")
    rule = CategoryRule(2, category_id=7, keyword="滴滴", field=RuleField.COUNTERPARTY)
    assert match_category(tx, [rule]) == 7


def test_case_insensitive_match():
    tx = make_tx("t3", 1000, Direction.EXPENSE, item_name="STARBUCKS 咖啡")
    rule = CategoryRule(3, category_id=10, keyword="starbucks")
    assert match_category(tx, [rule]) == 10


def test_custom_rule_beats_system_rule():
    tx = make_tx("t4", 1000, Direction.EXPENSE, item_name="咖啡")
    system = CategoryRule(1, category_id=99, keyword="咖啡", source=RuleSource.SYSTEM)
    custom = CategoryRule(2, category_id=10, keyword="咖啡", source=RuleSource.CUSTOM)
    assert match_category(tx, [system, custom]) == 10


def test_lower_priority_number_wins_within_same_source():
    tx = make_tx("t5", 1000, Direction.EXPENSE, item_name="咖啡拿铁")
    low = CategoryRule(1, category_id=10, keyword="咖啡", priority=1)
    high = CategoryRule(2, category_id=20, keyword="拿铁", priority=5)
    assert match_category(tx, [high, low]) == 10


def test_no_match_returns_none():
    tx = make_tx("t6", 1000, Direction.EXPENSE, item_name="未知杂项")
    rule = CategoryRule(1, category_id=10, keyword="咖啡")
    assert match_category(tx, [rule]) is None


def test_apply_classification_splits_inbox():
    txs = [
        make_tx("a", 1000, Direction.EXPENSE, item_name="咖啡"),
        make_tx("b", 1000, Direction.EXPENSE, item_name="神秘商品"),
    ]
    rules = [CategoryRule(1, category_id=10, keyword="咖啡")]
    classified, inbox = apply_classification(txs, rules)
    assert len(classified) == 1 and classified[0].category_id == 10
    assert len(inbox) == 1 and inbox[0].category_id is None
