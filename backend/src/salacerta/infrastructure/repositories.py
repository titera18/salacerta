"""Repositórios SQLAlchemy. Os agregados nunca herdam do ORM; a conversão acontece aqui."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salacerta.domain.booking import Booking
from salacerta.domain.room import Room
from salacerta.domain.value_objects import BookingStatus, EmailAddress, TimeSlot
from salacerta.infrastructure.database import BookingModel, RoomModel


def _room_to_domain(model: RoomModel) -> Room:
    return Room(
        id=UUID(model.id),
        name=model.name,
        capacity=model.capacity,
        is_active=model.is_active,
    )


def _room_to_model(room: Room) -> RoomModel:
    return RoomModel(
        id=str(room.id),
        name=room.name,
        capacity=room.capacity,
        is_active=room.is_active,
    )


def _booking_to_domain(model: BookingModel) -> Booking:
    return Booking(
        id=UUID(model.id),
        room_id=UUID(model.room_id),
        title=model.title,
        organizer=EmailAddress(model.organizer),
        attendees=model.attendees,
        slot=TimeSlot(model.start, model.end),
        status=BookingStatus(model.status),
    )


def _booking_to_model(booking: Booking) -> BookingModel:
    return BookingModel(
        id=str(booking.id),
        room_id=str(booking.room_id),
        title=booking.title,
        organizer=str(booking.organizer),
        attendees=booking.attendees,
        start=booking.slot.start,
        end=booking.slot.end,
        status=booking.status.value,
    )


class SqlAlchemyRoomRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, room: Room) -> None:
        self._session.add(_room_to_model(room))

    def save(self, room: Room) -> None:
        self._session.merge(_room_to_model(room))

    def get(self, room_id: UUID) -> Room | None:
        model = self._session.get(RoomModel, str(room_id))
        return _room_to_domain(model) if model else None

    def get_locked(self, room_id: UUID) -> Room | None:
        # No PostgreSQL vira SELECT ... FOR UPDATE; o SQLite ignora a trava.
        model = self._session.get(RoomModel, str(room_id), with_for_update=True)
        return _room_to_domain(model) if model else None

    def find_by_name(self, name: str) -> Room | None:
        statement = select(RoomModel).where(func.lower(RoomModel.name) == name.lower())
        model = self._session.scalar(statement)
        return _room_to_domain(model) if model else None

    def list_all(self) -> Sequence[Room]:
        models = self._session.scalars(select(RoomModel).order_by(RoomModel.name))
        return [_room_to_domain(model) for model in models]


class SqlAlchemyBookingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, booking: Booking) -> None:
        self._session.add(_booking_to_model(booking))

    def save(self, booking: Booking) -> None:
        self._session.merge(_booking_to_model(booking))

    def get(self, booking_id: UUID) -> Booking | None:
        model = self._session.get(BookingModel, str(booking_id))
        return _booking_to_domain(model) if model else None

    def find_overlapping(self, room_id: UUID, slot: TimeSlot) -> Sequence[Booking]:
        return self.list_between(slot.start, slot.end, room_id)

    def list_between(
        self, start: datetime, end: datetime, room_id: UUID | None = None
    ) -> Sequence[Booking]:
        statement = (
            select(BookingModel)
            .where(
                BookingModel.status == BookingStatus.SCHEDULED.value,
                BookingModel.start < end,
                BookingModel.end > start,
            )
            .order_by(BookingModel.start)
        )
        if room_id is not None:
            statement = statement.where(BookingModel.room_id == str(room_id))
        return [_booking_to_domain(model) for model in self._session.scalars(statement)]
