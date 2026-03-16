"""数据库会话管理。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.config.settings import get_settings
from shared.db.base import Base


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        raw_path = settings.database_url.split("///", maxsplit=1)[-1]
        sqlite_path = Path(raw_path)
        if sqlite_path.parent != Path():
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(settings.database_url, future=True, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def session_scope() -> Session:
    return get_session_factory()()


def init_db() -> None:
    from shared.models import tables  # noqa: F401

    Base.metadata.create_all(get_engine())
