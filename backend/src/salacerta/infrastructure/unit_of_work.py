from types import TracebackType
from typing import Any, Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from salacerta.domain.errors import RoomNameTaken
from salacerta.domain.repositories import BookingRepository, RoomRepository
from salacerta.infrastructure.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyRoomRepository,
)


class SqlAlchemyUnitOfWork:
    rooms: RoomRepository
    bookings: BookingRepository
    _session: Session

    def __init__(self, session_factory: sessionmaker[Any]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.rooms = SqlAlchemyRoomRepository(self._session)
        self.bookings = SqlAlchemyBookingRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as error:
            # A única restrição de unicidade do modelo é o nome da sala: chegar aqui
            # significa que duas criações simultâneas passaram pela checagem prévia.
            self._session.rollback()
            raise RoomNameTaken() from error
