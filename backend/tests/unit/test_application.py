"""Casos de uso testados com um Unit of Work em memória, sem banco e sem HTTP."""

from collections.abc import Sequence
from datetime import datetime, timedelta
from types import TracebackType
from typing import Self
from uuid import UUID, uuid4

import pytest

from salacerta.application.bookings import CancelBooking, ScheduleBooking
from salacerta.application.dtos import ScheduleBookingCommand
from salacerta.application.rooms import CreateRoom, SetRoomActive
from salacerta.domain.booking import Booking
from salacerta.domain.errors import (
    BookingConflict,
    BookingNotFound,
    RoomInactive,
    RoomNameTaken,
    RoomNotFound,
)
from salacerta.domain.events import BookingCancelled, BookingScheduled
from salacerta.domain.room import Room
from salacerta.domain.value_objects import BookingStatus, TimeSlot
from tests.conftest import NOW, FixedClock, SpyPublisher


class InMemoryRooms:
    def __init__(self) -> None:
        self.items: dict[UUID, Room] = {}

    def add(self, room: Room) -> None:
        self.items[room.id] = room

    save = add

    def get(self, room_id: UUID) -> Room | None:
        return self.items.get(room_id)

    get_locked = get

    def find_by_name(self, name: str) -> Room | None:
        return next((r for r in self.items.values() if r.name.lower() == name.lower()), None)

    def list_all(self) -> Sequence[Room]:
        return list(self.items.values())


class InMemoryBookings:
    def __init__(self) -> None:
        self.items: dict[UUID, Booking] = {}

    def add(self, booking: Booking) -> None:
        self.items[booking.id] = booking

    save = add

    def get(self, booking_id: UUID) -> Booking | None:
        return self.items.get(booking_id)

    def find_overlapping(self, room_id: UUID, slot: TimeSlot) -> Sequence[Booking]:
        return self.list_between(slot.start, slot.end, room_id)

    def list_between(
        self, start: datetime, end: datetime, room_id: UUID | None = None
    ) -> Sequence[Booking]:
        return [
            b
            for b in self.items.values()
            if b.status is BookingStatus.SCHEDULED
            and b.slot.start < end
            and b.slot.end > start
            and (room_id is None or b.room_id == room_id)
        ]


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.rooms = InMemoryRooms()
        self.bookings = InMemoryBookings()
        self.commits = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1


@pytest.fixture
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture
def room(uow: InMemoryUnitOfWork) -> Room:
    room = Room.create("Aurora", 10)
    uow.rooms.add(room)
    return room


def command(room_id: UUID, hours_ahead: int = 2) -> ScheduleBookingCommand:
    start = NOW + timedelta(hours=hours_ahead)
    return ScheduleBookingCommand(
        room_id=room_id,
        title="Planejamento",
        organizer="ana@empresa.com",
        attendees=4,
        start=start,
        end=start + timedelta(hours=1),
    )


def test_create_room_commits(uow: InMemoryUnitOfWork) -> None:
    view = CreateRoom(uow).execute("Aurora", 10)
    assert view.id in uow.rooms.items
    assert uow.commits == 1


def test_create_room_rejects_duplicate_name_ignoring_case(
    uow: InMemoryUnitOfWork, room: Room
) -> None:
    with pytest.raises(RoomNameTaken):
        CreateRoom(uow).execute("AURORA", 5)
    assert uow.commits == 0


def test_set_room_active_unknown_room(uow: InMemoryUnitOfWork) -> None:
    with pytest.raises(RoomNotFound):
        SetRoomActive(uow).execute(uuid4(), active=False)


def test_schedule_persists_and_publishes_after_commit(
    uow: InMemoryUnitOfWork, room: Room, publisher: SpyPublisher, clock: FixedClock
) -> None:
    view = ScheduleBooking(uow, publisher, clock).execute(command(room.id))

    assert view.status == "scheduled"
    assert uow.commits == 1
    assert [type(event) for event in publisher.events] == [BookingScheduled]


def test_schedule_unknown_room(
    uow: InMemoryUnitOfWork, publisher: SpyPublisher, clock: FixedClock
) -> None:
    with pytest.raises(RoomNotFound):
        ScheduleBooking(uow, publisher, clock).execute(command(uuid4()))


def test_failed_schedule_publishes_nothing(
    uow: InMemoryUnitOfWork, room: Room, publisher: SpyPublisher, clock: FixedClock
) -> None:
    use_case = ScheduleBooking(uow, publisher, clock)
    use_case.execute(command(room.id))
    publisher.events.clear()

    with pytest.raises(BookingConflict):
        use_case.execute(command(room.id))

    assert publisher.events == []
    assert uow.commits == 1


def test_schedule_in_deactivated_room(
    uow: InMemoryUnitOfWork, room: Room, publisher: SpyPublisher, clock: FixedClock
) -> None:
    SetRoomActive(uow).execute(room.id, active=False)
    with pytest.raises(RoomInactive):
        ScheduleBooking(uow, publisher, clock).execute(command(room.id))


def test_cancel_frees_the_slot(
    uow: InMemoryUnitOfWork, room: Room, publisher: SpyPublisher, clock: FixedClock
) -> None:
    schedule = ScheduleBooking(uow, publisher, clock)
    booking = schedule.execute(command(room.id))

    cancelled = CancelBooking(uow, publisher, clock).execute(booking.id)

    assert cancelled.status == "cancelled"
    assert isinstance(publisher.events[-1], BookingCancelled)
    assert schedule.execute(command(room.id)).status == "scheduled"


def test_cancel_unknown_booking(
    uow: InMemoryUnitOfWork, publisher: SpyPublisher, clock: FixedClock
) -> None:
    with pytest.raises(BookingNotFound):
        CancelBooking(uow, publisher, clock).execute(uuid4())
