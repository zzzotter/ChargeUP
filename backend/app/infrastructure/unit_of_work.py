"""SQLAlchemy 工作单元：一次用例一个会话、一个事务。"""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.repositories import (
    SqlAlchemyBudgetEventRepository,
    SqlAlchemyBudgetRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyImportRecordRepository,
    SqlAlchemyRuleRepository,
    SqlAlchemySettingsRepository,
    SqlAlchemyTransactionRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.transactions: SqlAlchemyTransactionRepository
        self.categories: SqlAlchemyCategoryRepository
        self.rules: SqlAlchemyRuleRepository
        self.budgets: SqlAlchemyBudgetRepository
        self.budget_events: SqlAlchemyBudgetEventRepository
        self.imports: SqlAlchemyImportRecordRepository
        self.settings: SqlAlchemySettingsRepository

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.transactions = SqlAlchemyTransactionRepository(self._session)
        self.categories = SqlAlchemyCategoryRepository(self._session)
        self.rules = SqlAlchemyRuleRepository(self._session)
        self.budgets = SqlAlchemyBudgetRepository(self._session)
        self.budget_events = SqlAlchemyBudgetEventRepository(self._session)
        self.imports = SqlAlchemyImportRecordRepository(self._session)
        self.settings = SqlAlchemySettingsRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        session = self._session
        self._session = None
        if session is None:
            return
        try:
            if exc_type is not None:
                session.rollback()
        finally:
            session.close()

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("UnitOfWork 未进入上下文")
        return self._session

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
