"""Serviço de domínio: a regra de agendamento envolve dois agregados, Room e Booking."""

from collections.abc import Iterable
from datetime import datetime

from salacerta.domain.booking import Booking
from salacerta.domain.errors import BookingConflict
from salacerta.domain.room import Room
from salacerta.domain.value_objects import EmailAddress, TimeSlot


def schedule_booking(
    room: Room,
    title: str,
    organizer: EmailAddress,
    attendees: int,
    slot: TimeSlot,
    existing: Iterable[Booking],
    now: datetime,
) -> Booking:
    room.ensure_can_host(attendees)
    if any(booking.slot.overlaps(slot) for booking in existing):
        raise BookingConflict()
    return Booking.schedule(room.id, title, organizer, attendees, slot, now)
