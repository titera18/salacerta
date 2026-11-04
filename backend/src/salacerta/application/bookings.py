from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from salacerta.application.dtos import BookingView, ScheduleBookingCommand
from salacerta.application.ports import Clock, EventPublisher, UnitOfWork
from salacerta.domain.errors import BookingNotFound, RoomNotFound
from salacerta.domain.services import schedule_booking
from salacerta.domain.value_objects import EmailAddress, TimeSlot


@dataclass(frozen=True)
class ScheduleBooking:
    uow: UnitOfWork
    publisher: EventPublisher
    clock: Clock

    def execute(self, command: ScheduleBookingCommand) -> BookingView:
        slot = TimeSlot(command.start, command.end)
        organizer = EmailAddress(command.organizer)

        with self.uow as uow:
            # A trava na sala garante que duas requisições simultâneas não
            # passem juntas pela verificação de conflito.
            room = uow.rooms.get_locked(command.room_id)
            if room is None:
                raise RoomNotFound()

            booking = schedule_booking(
                room=room,
                title=command.title,
                organizer=organizer,
                attendees=command.attendees,
                slot=slot,
                existing=uow.bookings.find_overlapping(room.id, slot),
                now=self.clock.now(),
            )
            uow.bookings.add(booking)
            uow.commit()

        self.publisher.publish(booking.pull_events())
        return BookingView.from_booking(booking)


@dataclass(frozen=True)
class CancelBooking:
    uow: UnitOfWork
    publisher: EventPublisher
    clock: Clock

    def execute(self, booking_id: UUID) -> BookingView:
        with self.uow as uow:
            booking = uow.bookings.get(booking_id)
            if booking is None:
                raise BookingNotFound()
            booking.cancel(self.clock.now())
            uow.bookings.save(booking)
            uow.commit()

        self.publisher.publish(booking.pull_events())
        return BookingView.from_booking(booking)


@dataclass(frozen=True)
class ListBookings:
    uow: UnitOfWork

    def execute(
        self, start: datetime, end: datetime, room_id: UUID | None = None
    ) -> list[BookingView]:
        with self.uow as uow:
            bookings = uow.bookings.list_between(start, end, room_id)
            return [BookingView.from_booking(booking) for booking in bookings]
