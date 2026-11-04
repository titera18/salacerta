from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from salacerta.application.bookings import ScheduleBooking
from salacerta.application.dtos import ScheduleBookingCommand
from salacerta.application.rooms import CreateRoom
from salacerta.domain.errors import BookingConflict
from salacerta.infrastructure.database import Base, build_engine
from salacerta.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from tests.conftest import NOW, FixedClock, SpyPublisher

BACKEND_ROOT = Path(__file__).parents[2]


def test_migrations_match_models(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    config = Config(BACKEND_ROOT / "alembic.ini")
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url)

    command.upgrade(config, "head")

    engine = build_engine(url)
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    engine.dispose()
    assert diff == []


def test_concurrent_requests_cannot_double_book(
    engine: Engine, session_factory: sessionmaker[Any]
) -> None:
    """Só o PostgreSQL trava a linha; o CI roda este teste contra um banco real."""
    if engine.dialect.name != "postgresql":
        pytest.skip("requer PostgreSQL (defina TEST_DATABASE_URL)")

    room = CreateRoom(SqlAlchemyUnitOfWork(session_factory)).execute("Aurora", 10)
    request = ScheduleBookingCommand(
        room_id=room.id,
        title="Planejamento",
        organizer="ana@empresa.com",
        attendees=2,
        start=NOW + timedelta(days=1),
        end=NOW + timedelta(days=1, hours=1),
    )
    workers = 8
    barrier = Barrier(workers)

    def attempt(_: int) -> str:
        use_case = ScheduleBooking(
            SqlAlchemyUnitOfWork(session_factory), SpyPublisher(), FixedClock()
        )
        barrier.wait()
        try:
            use_case.execute(request)
        except BookingConflict:
            return "conflict"
        return "scheduled"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(attempt, range(workers)))

    assert results.count("scheduled") == 1
    assert results.count("conflict") == workers - 1
