"""SQLAlchemy 2.x 映射模型。领域层不引用本模块。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CategoryModel(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CategoryRuleModel(Base):
    __tablename__ = "category_rules"
    __table_args__ = (
        UniqueConstraint("keyword", "category_id", "is_builtin", name="uq_category_rules_keyword"),
        Index("ix_category_rules_builtin", "is_builtin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        # 幂等去重：同一来源下外部单号唯一（软删除记录同样占用单号，避免重复导入）
        UniqueConstraint("source", "external_id", name="uq_transactions_source_external_id"),
        Index("ix_transactions_occurred_at", "occurred_at"),
        Index("ix_transactions_category_id", "category_id"),
        Index("ix_transactions_refund_of", "refund_of_transaction_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    merchant: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    note: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    category_source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    refund_of_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BudgetModel(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("period", name="uq_budgets_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    warn_bps: Mapped[int] = mapped_column(Integer, nullable=False, default=8000, server_default="8000")
    alert_bps: Mapped[int] = mapped_column(Integer, nullable=False, default=10000, server_default="10000")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BudgetEventModel(Base):
    __tablename__ = "budget_events"
    __table_args__ = (
        # 同一周期同一级别只触发一次
        UniqueConstraint("period", "level", name="uq_budget_events_period_level"),
        Index("ix_budget_events_budget_id", "budget_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    spent_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    threshold_bps: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportRecordModel(Base):
    __tablename__ = "import_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    encoding: Mapped[str] = mapped_column(String(32), nullable=False, default="utf-8", server_default="utf-8")
    recognized: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    skipped_header_rows: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    duplicated: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failures: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AppSettingsModel(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hourly_rate_cents: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    persona: Mapped[str] = mapped_column(
        String(16), nullable=False, default="RATIONAL", server_default="RATIONAL"
    )
    module_wardrobe: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    module_intents: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    module_feedback: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
