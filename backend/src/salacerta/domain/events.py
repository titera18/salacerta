from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from salacerta.domain.base import DomainEvent


@dataclass(frozen=True, kw_only=True)
class BookingScheduled(DomainEvent):
    booking_id: UUID
    room_id: UUID
    organizer: str
    start: datetime
    end: datetime
    occurred_at: datetime


@dataclass(frozen=True, kw_only=True)
class BookingCancelled(DomainEvent):
    booking_id: UUID
    room_id: UUID
    occurred_at: datetime
