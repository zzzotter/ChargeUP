"""对齐前端接口契约（页面清单 §7）

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-27

变更：
- transactions.category_source：分类来源（RULE/BUILTIN/USER/null）
- categories.color / is_active：分类改色与停用
- budget_events.threshold_bps / read：预警阈值快照与已读状态
- import_records：导入历史与失败明细
- app_settings：时薪 / 人设 / 模块开关
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("category_source", sa.String(length=16), nullable=True))
    op.add_column("categories", sa.Column("color", sa.String(length=16), nullable=True))
    op.add_column(
        "categories",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "budget_events",
        sa.Column("threshold_bps", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "budget_events",
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "import_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("encoding", sa.String(length=32), nullable=False, server_default="utf-8"),
        sa.Column("recognized", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_header_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failures", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hourly_rate_cents", sa.BigInteger(), nullable=True),
        sa.Column("persona", sa.String(length=16), nullable=False, server_default="RATIONAL"),
        sa.Column("module_wardrobe", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("module_intents", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("module_feedback", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("import_records")
    op.drop_column("budget_events", "read")
    op.drop_column("budget_events", "threshold_bps")
    op.drop_column("categories", "is_active")
    op.drop_column("categories", "color")
    op.drop_column("transactions", "category_source")
