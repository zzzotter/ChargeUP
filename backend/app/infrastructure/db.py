"""数据库连接与会话管理（引擎惰性创建，便于无 PG 驱动的环境下跑测试）。"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.models import Base
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

_MEMORY_URLS = ("sqlite://", "sqlite+pysqlite://", "sqlite:///:memory:")


class Database:
    def __init__(self, url: str, *, echo: bool = False) -> None:
        self._url = url
        self._echo = echo
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            kwargs: dict = {}
            connect_args: dict = {}
            if self._url.startswith("sqlite"):
                connect_args["check_same_thread"] = False
                if self._url in _MEMORY_URLS:
                    kwargs["poolclass"] = StaticPool
            self._engine = create_engine(
                self._url, echo=self._echo, connect_args=connect_args, **kwargs
            )
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine, expire_on_commit=False, autoflush=False
            )
        return self._session_factory

    def create_schema(self) -> None:
        """开发/测试用；生产环境走 Alembic 迁移。"""
        Base.metadata.create_all(self.engine)

    def drop_schema(self) -> None:
        Base.metadata.drop_all(self.engine)

    def unit_of_work(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory)

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
