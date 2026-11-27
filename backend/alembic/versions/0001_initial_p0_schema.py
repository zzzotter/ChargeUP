"""P0 初始表结构：分类、规则、交易、预算、预警事件

Revision ID: 0001
Revises:
Create Date: 2026-11-25

要点：
- 金额一律 integer（分），杜绝浮点；
- 交易不物理删除，deleted_at 表达软删除；
- (source, external_id) 唯一，保证导入幂等。
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )

    op.create_table(
        "category_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keyword", sa.String(length=64), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("keyword", "category_id", "is_builtin", name="uq_category_rules_keyword"),
    )
    op.create_index("ix_category_rules_builtin", "category_rules", ["is_builtin"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False, comment="金额（整数分）"),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("merchant", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("refund_of_transaction_id", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="软删除标记"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["refund_of_transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id", name="uq_transactions_source_external_id"),
    )
    op.create_index("ix_transactions_occurred_at", "transactions", ["occurred_at"])
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])
    op.create_index("ix_transactions_refund_of", "transactions", ["refund_of_transaction_id"])

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False, comment="YYYY-MM"),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("warn_bps", sa.Integer(), nullable=False, server_default="8000"),
        sa.Column("alert_bps", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("period", name="uq_budgets_period"),
    )

    op.create_table(
        "budget_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("budget_id", sa.Integer(), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("spent_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("period", "level", name="uq_budget_events_period_level"),
    )
    op.create_index("ix_budget_events_budget_id", "budget_events", ["budget_id"])


def downgrade() -> None:
    op.drop_index("ix_budget_events_budget_id", table_name="budget_events")
    op.drop_table("budget_events")
    op.drop_table("budgets")
    op.drop_index("ix_transactions_refund_of", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_index("ix_transactions_occurred_at", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_category_rules_builtin", table_name="category_rules")
    op.drop_table("category_rules")
    op.drop_table("categories")
