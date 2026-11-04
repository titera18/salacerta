"""Contratos de persistência definidos pelo domínio e implementados na infraestrutura."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from salacerta.domain.booking import Booking
from salacerta.domain.room import Room
from salacerta.domain.value_objects import TimeSlot


class RoomRepository(Protocol):
    def add(self, room: Room) -> None: ...

    def save(self, room: Room) -> None: ...

    def get(self, room_id: UUID) -> Room | None: ...

    def get_locked(self, room_id: UUID) -> Room | None:
        """Carrega a sala travando-a até o fim da transação, serializando os agendamentos."""
        ...

    def find_by_name(self, name: str) -> Room | None: ...

    def list_all(self) -> Sequence[Room]: ...


class BookingRepository(Protocol):
    def add(self, booking: Booking) -> None: ...

    def save(self, booking: Booking) -> None: ...

    def get(self, booking_id: UUID) -> Booking | None: ...

    def find_overlapping(self, room_id: UUID, slot: TimeSlot) -> Sequence[Booking]:
        """Retorna apenas as reservas ativas que colidem com o intervalo."""
        ...

    def list_between(
        self, start: datetime, end: datetime, room_id: UUID | None = None
    ) -> Sequence[Booking]:
        """Retorna as reservas ativas que têm alguma parte dentro do período."""
        ...
