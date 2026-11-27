"""退款关联与转账排除（第 8 天，纯领域逻辑）。

退款配对条件：
- 原消费为 EXPENSE，候选退款为 INCOME；
- 退款金额不超过原消费金额（支持全额/部分退款）；
- 退款时间不早于消费、且在 window_days（默认 7 天）内；
- 对方或商品名称匹配（退款单常见“原名称-退款”，做包含匹配）；
- 一笔消费最多配对一次，一笔退款只使用一次。
"""
from dataclasses import dataclass
from datetime import timedelta

from ..parser.models import Direction, RawTransaction


@dataclass(frozen=True)
class RefundPair:
    expense: RawTransaction
    refund: RawTransaction
    full_refund: bool


def _name_match(expense: RawTransaction, refund: RawTransaction) -> bool:
    e_name = (expense.item_name or expense.counterparty or "").lower()
    r_name = (refund.item_name or refund.counterparty or "").lower()
    if not e_name or not r_name:
        return False
    # 去掉退款后缀后做双向包含，如 “益禾堂” 与 “益禾堂-退款”
    r_clean = r_name.replace("-退款", "").replace("退款", "").strip()
    return r_clean in e_name or e_name in r_clean or e_name in r_name


def find_refund_pairs(
    transactions: list[RawTransaction], window_days: int = 7
) -> list[RefundPair]:
    expenses = [
        tx for tx in transactions
        if tx.direction == Direction.EXPENSE and tx.amount_cents > 0
    ]
    refunds = [
        tx for tx in transactions if tx.direction == Direction.INCOME
    ]
    used_refund_ids: set[str] = set()
    pairs: list[RefundPair] = []

    # 按消费时间顺序处理，保证结果稳定
    for expense in sorted(expenses, key=lambda t: t.transacted_at):
        window_end = expense.transacted_at + timedelta(days=window_days)
        for refund in sorted(refunds, key=lambda t: t.transacted_at):
            if refund.external_id in used_refund_ids:
                continue
            if not (expense.transacted_at <= refund.transacted_at <= window_end):
                continue
            if refund.amount_cents > expense.amount_cents:
                continue
            if not _name_match(expense, refund):
                continue
            used_refund_ids.add(refund.external_id)
            pairs.append(RefundPair(
                expense=expense,
                refund=refund,
                full_refund=(refund.amount_cents == expense.amount_cents),
            ))
            break
    return pairs


def is_transfer(tx: RawTransaction) -> bool:
    """转账/中性交易在支出统计中强制排除。"""
    return tx.direction == Direction.TRANSFER
