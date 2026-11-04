from dataclasses import dataclass
from uuid import UUID, uuid4

from salacerta.domain.base import AggregateRoot
from salacerta.domain.errors import CapacityExceeded, InvalidRoom, RoomInactive

MAX_CAPACITY = 500


@dataclass(eq=False)
class Room(AggregateRoot):
    name: str
    capacity: int
    is_active: bool = True

    @classmethod
    def create(cls, name: str, capacity: int, room_id: UUID | None = None) -> "Room":
        name = name.strip()
        if not 2 <= len(name) <= 60:
            raise InvalidRoom("O nome da sala precisa ter entre 2 e 60 caracteres.")
        if not 1 <= capacity <= MAX_CAPACITY:
            raise InvalidRoom(f"A capacidade precisa estar entre 1 e {MAX_CAPACITY} pessoas.")
        return cls(id=room_id or uuid4(), name=name, capacity=capacity)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def ensure_can_host(self, attendees: int) -> None:
        if not self.is_active:
            raise RoomInactive()
        if attendees > self.capacity:
            raise CapacityExceeded(
                f"A sala {self.name} comporta no máximo {self.capacity} pessoas."
            )
