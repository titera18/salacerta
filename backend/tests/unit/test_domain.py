from datetime import UTC, datetime, timedelta, timezone

import pytest

from salacerta.domain.booking import Booking
from salacerta.domain.errors import (
    BookingConflict,
    BookingInPast,
    BookingNotCancellable,
    CapacityExceeded,
    InvalidBooking,
    InvalidEmail,
    InvalidRoom,
    InvalidTimeSlot,
    RoomInactive,
)
from salacerta.domain.events import BookingCancelled, BookingScheduled
from salacerta.domain.room import Room
from salacerta.domain.services import schedule_booking
from salacerta.domain.value_objects import BookingStatus, EmailAddress, TimeSlot

NOW = datetime(2030, 1, 7, 12, 0, tzinfo=UTC)
ORGANIZER = EmailAddress("ana@empresa.com")


def slot(start_hour: int = 14, end_hour: int = 15) -> TimeSlot:
    return TimeSlot(NOW.replace(hour=start_hour), NOW.replace(hour=end_hour))


def make_booking(booking_slot: TimeSlot | None = None) -> Booking:
    room = Room.create("Aurora", 10)
    return Booking.schedule(room.id, "Planejamento", ORGANIZER, 4, booking_slot or slot(), NOW)


class TestTimeSlot:
    def test_converts_to_utc(self) -> None:
        brasilia = timezone(timedelta(hours=-3))
        value = TimeSlot(
            datetime(2030, 1, 7, 9, tzinfo=brasilia),
            datetime(2030, 1, 7, 10, tzinfo=brasilia),
        )
        assert value.start == datetime(2030, 1, 7, 12, tzinfo=UTC)
        assert value.start.tzinfo is UTC

    @pytest.mark.parametrize(
        ("start", "end"),
        [
            (NOW, NOW),
            (NOW, NOW - timedelta(hours=1)),
            (NOW, NOW + timedelta(minutes=14)),
            (NOW, NOW + timedelta(hours=8, minutes=1)),
            (NOW.replace(tzinfo=None), NOW + timedelta(hours=1)),
        ],
        ids=["zero", "inverted", "too-short", "too-long", "naive"],
    )
    def test_rejects_invalid_ranges(self, start: datetime, end: datetime) -> None:
        with pytest.raises(InvalidTimeSlot):
            TimeSlot(start, end)

    def test_detects_overlap(self) -> None:
        assert slot(14, 16).overlaps(slot(15, 17))
        assert slot(14, 18).overlaps(slot(15, 16))

    def test_adjacent_slots_do_not_overlap(self) -> None:
        assert not slot(14, 15).overlaps(slot(15, 16))
        assert not slot(15, 16).overlaps(slot(14, 15))


class TestEmailAddress:
    def test_normalizes(self) -> None:
        assert str(EmailAddress("  Ana@Empresa.COM ")) == "ana@empresa.com"

    @pytest.mark.parametrize("value", ["", "ana", "ana@empresa", "a b@empresa.com"])
    def test_rejects_invalid(self, value: str) -> None:
        with pytest.raises(InvalidEmail):
            EmailAddress(value)


class TestRoom:
    def test_create_trims_name(self) -> None:
        assert Room.create("  Aurora ", 10).name == "Aurora"

    @pytest.mark.parametrize(
        ("name", "capacity"), [("A", 10), ("x" * 61, 10), ("Aurora", 0), ("Aurora", 501)]
    )
    def test_rejects_invalid_data(self, name: str, capacity: int) -> None:
        with pytest.raises(InvalidRoom):
            Room.create(name, capacity)

    def test_identity_defines_equality(self) -> None:
        room = Room.create("Aurora", 10)
        assert room == Room(id=room.id, name="Outro nome", capacity=1)
        assert room != Room.create("Aurora", 10)


class TestBooking:
    def test_schedule_records_event(self) -> None:
        booking = make_booking()
        events = booking.pull_events()
        assert booking.status is BookingStatus.SCHEDULED
        assert [type(event) for event in events] == [BookingScheduled]
        assert booking.pull_events() == []

    @pytest.mark.parametrize(("title", "attendees"), [("ab", 1), ("x" * 121, 1), ("Daily", 0)])
    def test_rejects_invalid_data(self, title: str, attendees: int) -> None:
        room = Room.create("Aurora", 10)
        with pytest.raises(InvalidBooking):
            Booking.schedule(room.id, title, ORGANIZER, attendees, slot(), NOW)

    def test_rejects_start_in_the_past(self) -> None:
        with pytest.raises(BookingInPast):
            make_booking(TimeSlot(NOW, NOW + timedelta(hours=1)))

    def test_cancel(self) -> None:
        booking = make_booking()
        booking.pull_events()
        booking.cancel(NOW)
        assert booking.status is BookingStatus.CANCELLED
        assert [type(event) for event in booking.pull_events()] == [BookingCancelled]

    def test_cannot_cancel_twice(self) -> None:
        booking = make_booking()
        booking.cancel(NOW)
        with pytest.raises(BookingNotCancellable):
            booking.cancel(NOW)

    def test_cannot_cancel_after_start(self) -> None:
        booking = make_booking()
        with pytest.raises(BookingNotCancellable):
            booking.cancel(booking.slot.start)


class TestScheduleBookingService:
    def test_schedules_when_rules_pass(self) -> None:
        room = Room.create("Aurora", 10)
        booking = schedule_booking(room, "Daily", ORGANIZER, 10, slot(), [], NOW)
        assert booking.room_id == room.id

    def test_rejects_conflict(self) -> None:
        room = Room.create("Aurora", 10)
        with pytest.raises(BookingConflict):
            schedule_booking(room, "Daily", ORGANIZER, 1, slot(14, 16), [make_booking()], NOW)

    def test_rejects_over_capacity(self) -> None:
        room = Room.create("Aurora", 2)
        with pytest.raises(CapacityExceeded):
            schedule_booking(room, "Daily", ORGANIZER, 3, slot(), [], NOW)

    def test_rejects_inactive_room(self) -> None:
        room = Room.create("Aurora", 10)
        room.deactivate()
        with pytest.raises(RoomInactive):
            schedule_booking(room, "Daily", ORGANIZER, 1, slot(), [], NOW)
