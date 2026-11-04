"""Contrato HTTP. Só valida formato; as regras de negócio ficam no domínio."""

from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict


class CreateRoomRequest(BaseModel):
    name: str
    capacity: int


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    capacity: int
    is_active: bool


class ScheduleBookingRequest(BaseModel):
    room_id: UUID
    title: str
    organizer: str
    attendees: int
    start: AwareDatetime
    end: AwareDatetime


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    title: str
    organizer: str
    attendees: int
    start: AwareDatetime
    end: AwareDatetime
    status: Literal["scheduled", "cancelled"]


class ErrorResponse(BaseModel):
    code: str
    message: str
