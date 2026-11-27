"""退款关联识别（SRS F-P0-03）。

只认定「看起来确实是退款」的配对，避免把普通收入（如工资）当成退款剔除：
1. 显式 `refund_of_transaction_id` 关联 —— 总是采信；
2. 自动匹配需同时满足：金额相同、方向相反、退款不早于原支出且间隔不超过 7 天、
   且（商户可对应 或 收入方带有退款语义关键词）。
商户无法对应且无退款语义的收入不参与配对，继续按普通收入计入统计。
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import timedelta

from app.domain.entities import Transaction
from app.domain.enums import Direction
from app.domain.services.categorization import normalize_text

DEFAULT_REFUND_WINDOW = timedelta(days=7)

# 退款语义关键词：用于在商户不一致时确认收入方确实是退款
_REFUND_HINTS = ("退款", "退货", "退单", "退还", "退回", "refund", "reversal")


@dataclass(frozen=True)
class RefundPair:
    original_id: int
    refund_id: int


def _merchant_matches(left: Transaction, right: Transaction) -> bool:
    left_name = normalize_text(left.merchant)
    right_name = normalize_text(right.merchant)
    if not left_name or not right_name:
        return False
    return left_name in right_name or right_name in left_name


def _looks_like_refund(transaction: Transaction) -> bool:
    text = normalize_text(f"{transaction.merchant} {transaction.note}")
    return any(hint in text for hint in _REFUND_HINTS)


def _is_auto_pairable(expense: Transaction, income: Transaction) -> bool:
    """自动配对必须能证明「这是同一笔消费的退款」，否则不动统计。"""
    return _merchant_matches(expense, income) or _looks_like_refund(income)


def detect_refund_pairs(
    transactions: Sequence[Transaction],
    window: timedelta = DEFAULT_REFUND_WINDOW,
) -> list[RefundPair]:
    """在给定交易集合内识别退款对，返回按退款时间排序的结果。"""
    known = {txn.id: txn for txn in transactions if txn.id is not None}
    used: set[int] = set()
    pairs: list[RefundPair] = []

    # 1. 尊重已存在的显式关联
    for txn in transactions:
        if txn.id is None or txn.refund_of_transaction_id is None:
            continue
        original = known.get(txn.refund_of_transaction_id)
        if original is None or original.id is None:
            continue
        if original.direction is txn.direction:
            continue
        used.update({txn.id, original.id})
        pairs.append(RefundPair(original_id=original.id, refund_id=txn.id))

    # 2. 自动匹配：金额相反 + 时间窗口内 + 可证明是退款
    expenses = [t for t in transactions if t.direction is Direction.EXPENSE and t.id is not None]
    incomes = sorted(
        (t for t in transactions if t.direction is Direction.INCOME and t.id is not None),
        key=lambda t: (t.occurred_at, t.id or 0),
    )

    for refund in incomes:
        if refund.id in used:
            continue
        best: tuple[tuple[int, int, int], Transaction] | None = None
        for expense in expenses:
            if expense.id in used or expense.amount_cents != refund.amount_cents:
                continue
            delta = refund.occurred_at - expense.occurred_at
            if delta < timedelta(0) or delta > window:
                continue
            if not _is_auto_pairable(expense, refund):
                continue
            same_merchant = 0 if _merchant_matches(expense, refund) else 1
            score = (same_merchant, int(delta.total_seconds()), expense.id or 0)
            if best is None or score < best[0]:
                best = (score, expense)
        if best is not None and best[1].id is not None and refund.id is not None:
            used.update({best[1].id, refund.id})
            pairs.append(RefundPair(original_id=best[1].id, refund_id=refund.id))

    pairs.sort(key=lambda pair: pair.refund_id)
    return pairs


def linked_transaction_ids(pairs: Iterable[RefundPair]) -> set[int]:
    """退款对涉及的所有交易 id（统计时全部剔除）。"""
    result: set[int] = set()
    for pair in pairs:
        result.add(pair.original_id)
        result.add(pair.refund_id)
    return result
