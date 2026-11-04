"""Raiz de composição: o único ponto que conhece as implementações concretas."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import sessionmaker

from salacerta.application.bookings import CancelBooking, ListBookings, ScheduleBooking
from salacerta.application.ports import Clock, EventPublisher
from salacerta.application.rooms import CreateRoom, ListRooms, SetRoomActive
from salacerta.infrastructure.adapters import LoggingEventPublisher, SystemClock
from salacerta.infrastructure.database import build_engine, build_session_factory
from salacerta.infrastructure.settings import Settings
from salacerta.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@dataclass(frozen=True)
class Container:
    session_factory: sessionmaker[Any]
    clock: Clock
    publisher: EventPublisher

    @classmethod
    def from_settings(cls, settings: Settings) -> "Container":
        return cls(
            session_factory=build_session_factory(build_engine(settings.database_url)),
            clock=SystemClock(),
            publisher=LoggingEventPublisher(),
        )

    def _uow(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory)

    def create_room(self) -> CreateRoom:
        return CreateRoom(self._uow())

    def list_rooms(self) -> ListRooms:
        return ListRooms(self._uow())

    def set_room_active(self) -> SetRoomActive:
        return SetRoomActive(self._uow())

    def schedule_booking(self) -> ScheduleBooking:
        return ScheduleBooking(self._uow(), self.publisher, self.clock)

    def cancel_booking(self) -> CancelBooking:
        return CancelBooking(self._uow(), self.publisher, self.clock)

    def list_bookings(self) -> ListBookings:
        return ListBookings(self._uow())
