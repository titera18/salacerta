from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from salacerta.domain.base import AggregateRoot
from salacerta.domain.errors import BookingInPast, BookingNotCancellable, InvalidBooking
from salacerta.domain.events import BookingCancelled, BookingScheduled
from salacerta.domain.value_objects import BookingStatus, EmailAddress, TimeSlot


@dataclass(eq=False)
class Booking(AggregateRoot):
    room_id: UUID
    title: str
    organizer: EmailAddress
    attendees: int
    slot: TimeSlot
    status: BookingStatus = BookingStatus.SCHEDULED

    @classmethod
    def schedule(
        cls,
        room_id: UUID,
        title: str,
        organizer: EmailAddress,
        attendees: int,
        slot: TimeSlot,
        now: datetime,
    ) -> "Booking":
        title = title.strip()
        if not 3 <= len(title) <= 120:
            raise InvalidBooking("O título precisa ter entre 3 e 120 caracteres.")
        if attendees < 1:
            raise InvalidBooking("A reserva precisa de pelo menos 1 participante.")
        if slot.start <= now:
            raise BookingInPast()

        booking = cls(
            id=uuid4(),
            room_id=room_id,
            title=title,
            organizer=organizer,
            attendees=attendees,
            slot=slot,
        )
        booking._record(
            BookingScheduled(
                booking_id=booking.id,
                room_id=room_id,
                organizer=str(organizer),
                start=slot.start,
                end=slot.end,
                occurred_at=now,
            )
        )
        return booking

    def cancel(self, now: datetime) -> None:
        if self.status is BookingStatus.CANCELLED:
            raise BookingNotCancellable("Esta reserva já foi cancelada.")
        if self.slot.start <= now:
            raise BookingNotCancellable("Uma reserva já iniciada não pode ser cancelada.")

        self.status = BookingStatus.CANCELLED
        self._record(BookingCancelled(booking_id=self.id, room_id=self.room_id, occurred_at=now))
