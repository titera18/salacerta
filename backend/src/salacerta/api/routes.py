from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import AwareDatetime

from salacerta.api.container import Container
from salacerta.api.schemas import (
    BookingResponse,
    CreateRoomRequest,
    ErrorResponse,
    RoomResponse,
    ScheduleBookingRequest,
)
from salacerta.application.dtos import BookingView, RoomView, ScheduleBookingCommand


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


ContainerDep = Annotated[Container, Depends(get_container)]

_NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorResponse}}
_CONFLICT: dict[int | str, dict[str, Any]] = {409: {"model": ErrorResponse}}

router = APIRouter(prefix="/api")


@router.get("/rooms", response_model=list[RoomResponse], tags=["rooms"])
def list_rooms(container: ContainerDep) -> list[RoomView]:
    return container.list_rooms().execute()


@router.post(
    "/rooms",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_CONFLICT,
    tags=["rooms"],
)
def create_room(body: CreateRoomRequest, container: ContainerDep) -> RoomView:
    return container.create_room().execute(body.name, body.capacity)


@router.post(
    "/rooms/{room_id}/deactivate",
    response_model=RoomResponse,
    responses=_NOT_FOUND,
    tags=["rooms"],
)
def deactivate_room(room_id: UUID, container: ContainerDep) -> RoomView:
    return container.set_room_active().execute(room_id, active=False)


@router.post(
    "/rooms/{room_id}/activate",
    response_model=RoomResponse,
    responses=_NOT_FOUND,
    tags=["rooms"],
)
def activate_room(room_id: UUID, container: ContainerDep) -> RoomView:
    return container.set_room_active().execute(room_id, active=True)


@router.get("/bookings", response_model=list[BookingResponse], tags=["bookings"])
def list_bookings(
    container: ContainerDep,
    start: Annotated[AwareDatetime, Query(description="Início do período")],
    end: Annotated[AwareDatetime, Query(description="Fim do período")],
    room_id: UUID | None = None,
) -> list[BookingView]:
    return container.list_bookings().execute(start, end, room_id)


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**_NOT_FOUND, **_CONFLICT},
    tags=["bookings"],
)
def schedule_booking(body: ScheduleBookingRequest, container: ContainerDep) -> BookingView:
    command = ScheduleBookingCommand(
        room_id=body.room_id,
        title=body.title,
        organizer=body.organizer,
        attendees=body.attendees,
        start=body.start,
        end=body.end,
    )
    return container.schedule_booking().execute(command)


@router.post(
    "/bookings/{booking_id}/cancel",
    response_model=BookingResponse,
    responses=_NOT_FOUND,
    tags=["bookings"],
)
def cancel_booking(booking_id: UUID, container: ContainerDep) -> BookingView:
    return container.cancel_booking().execute(booking_id)
