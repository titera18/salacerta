import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from salacerta.api.container import Container
from salacerta.api.main import create_app
from salacerta.domain.base import DomainEvent
from salacerta.infrastructure.database import Base, build_engine, build_session_factory

NOW = datetime(2030, 1, 7, 12, 0, tzinfo=UTC)


class FixedClock:
    def __init__(self, now: datetime = NOW) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


class SpyPublisher:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, events: Any) -> None:
        self.events.extend(events)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def publisher() -> SpyPublisher:
    return SpyPublisher()


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    """Usa SQLite por padrão; o CI aponta TEST_DATABASE_URL para o PostgreSQL."""
    url = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    engine = build_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Any]:
    return build_session_factory(engine)


@pytest.fixture
def client(
    session_factory: sessionmaker[Any], clock: FixedClock, publisher: SpyPublisher
) -> Iterator[TestClient]:
    container = Container(session_factory=session_factory, clock=clock, publisher=publisher)
    with TestClient(create_app(container)) as test_client:
        yield test_client
