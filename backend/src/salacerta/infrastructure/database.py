from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Engine, ForeignKey, Index, String, create_engine, func
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Sempre grava e devolve UTC, inclusive no SQLite, que não guarda fuso."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        return value.astimezone(UTC) if value is not None else None

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


class RoomModel(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    capacity: Mapped[int]
    is_active: Mapped[bool]

    __table_args__ = (Index("ux_rooms_name_lower", func.lower(name), unique=True),)


class BookingModel(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    room_id: Mapped[str] = mapped_column(String(36), ForeignKey("rooms.id"))
    title: Mapped[str] = mapped_column(String(120))
    organizer: Mapped[str] = mapped_column(String(254))
    attendees: Mapped[int]
    start: Mapped[datetime] = mapped_column("starts_at", UTCDateTime)
    end: Mapped[datetime] = mapped_column("ends_at", UTCDateTime)
    status: Mapped[str] = mapped_column(String(20))

    __table_args__ = (Index("ix_bookings_room_period", "room_id", "starts_at", "ends_at"),)


def build_engine(database_url: str) -> Engine:
    options: dict[str, Any] = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **options)


def build_session_factory(engine: Engine) -> sessionmaker[Any]:
    return sessionmaker(engine, expire_on_commit=False)
