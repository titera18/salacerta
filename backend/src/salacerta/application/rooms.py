from dataclasses import dataclass
from uuid import UUID

from salacerta.application.dtos import RoomView
from salacerta.application.ports import UnitOfWork
from salacerta.domain.errors import RoomNameTaken, RoomNotFound
from salacerta.domain.room import Room


@dataclass(frozen=True)
class CreateRoom:
    uow: UnitOfWork

    def execute(self, name: str, capacity: int) -> RoomView:
        room = Room.create(name, capacity)
        with self.uow as uow:
            if uow.rooms.find_by_name(room.name) is not None:
                raise RoomNameTaken()
            uow.rooms.add(room)
            uow.commit()
        return RoomView.from_room(room)


@dataclass(frozen=True)
class ListRooms:
    uow: UnitOfWork

    def execute(self) -> list[RoomView]:
        with self.uow as uow:
            return [RoomView.from_room(room) for room in uow.rooms.list_all()]


@dataclass(frozen=True)
class SetRoomActive:
    uow: UnitOfWork

    def execute(self, room_id: UUID, active: bool) -> RoomView:
        with self.uow as uow:
            room = uow.rooms.get_locked(room_id)
            if room is None:
                raise RoomNotFound()
            if active:
                room.activate()
            else:
                room.deactivate()
            uow.rooms.save(room)
            uow.commit()
        return RoomView.from_room(room)
