"""金额列升级为 BIGINT（金额上限 100 亿元，远超 32 位 INTEGER 的 2147 万元）

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-25

PostgreSQL 的 INTEGER 上限为 2147483647 分（约 2147 万元），
大额记账会溢出；领域层同时把单笔金额限制在 10^12 分以内。
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "transactions",
        "amount_cents",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )
    op.alter_column(
        "budgets",
        "amount_cents",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )
    op.alter_column(
        "budget_events",
        "spent_cents",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "budget_events",
        "spent_cents",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "budgets",
        "amount_cents",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "transactions",
        "amount_cents",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
