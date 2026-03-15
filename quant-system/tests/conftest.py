from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.strategy_registry.services.registry_service import RegistryService
from shared.db.base import Base
from shared.utils.state_store import InMemoryStateStore
from tests.helpers import seed_market_data


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def state_store() -> InMemoryStateStore:
    return InMemoryStateStore()


@pytest.fixture
def seeded_session(session: Session) -> Session:
    RegistryService().seed_default_strategies(session)
    seed_market_data(session, mode="trend")
    session.commit()
    return session
