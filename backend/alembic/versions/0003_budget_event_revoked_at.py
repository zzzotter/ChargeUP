"""预算预警事件支持失效标记（支出回落后撤销、再次越线重新激活）

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-25

背景：预算支出回落后，历史事件不应继续作为「当前已触发」展示；
但直接删除事件会丢失审计线索，因此增加 revoked_at：
- revoked_at IS NULL -> 当前生效；
- revoked_at 非空 -> 已失效，保留历史。
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "budget_events",
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("budget_events", "revoked_at")
