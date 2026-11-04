"""Dados que cruzam a fronteira da aplicação, para não expor os agregados."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from salacerta.domain.booking import Booking
from salacerta.domain.room import Room


@dataclass(frozen=True)
class RoomView:
    id: UUID
    name: str
    capacity: int
    is_active: bool

    @classmethod
    def from_room(cls, room: Room) -> "RoomView":
        return cls(room.id, room.name, room.capacity, room.is_active)


@dataclass(frozen=True)
class BookingView:
    id: UUID
    room_id: UUID
    title: str
    organizer: str
    attendees: int
    start: datetime
    end: datetime
    status: str

    @classmethod
    def from_booking(cls, booking: Booking) -> "BookingView":
        return cls(
            id=booking.id,
            room_id=booking.room_id,
            title=booking.title,
            organizer=str(booking.organizer),
            attendees=booking.attendees,
            start=booking.slot.start,
            end=booking.slot.end,
            status=booking.status.value,
        )


@dataclass(frozen=True)
class ScheduleBookingCommand:
    room_id: UUID
    title: str
    organizer: str
    attendees: int
    start: datetime
    end: datetime
