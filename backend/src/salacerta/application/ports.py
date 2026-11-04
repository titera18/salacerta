"""Portas que a aplicação exige do mundo externo."""

from collections.abc import Iterable
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self

from salacerta.domain.base import DomainEvent
from salacerta.domain.repositories import BookingRepository, RoomRepository


class UnitOfWork(Protocol):
    """Define o limite da transação. Sair do bloco sem `commit` descarta as alterações."""

    rooms: RoomRepository
    bookings: BookingRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...


class EventPublisher(Protocol):
    def publish(self, events: Iterable[DomainEvent]) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
