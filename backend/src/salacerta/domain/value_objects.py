"""Value objects: sem identidade, imutáveis e sempre válidos depois de criados."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from salacerta.domain.errors import InvalidEmail, InvalidTimeSlot

MIN_DURATION = timedelta(minutes=15)
MAX_DURATION = timedelta(hours=8)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BookingStatus(StrEnum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class EmailAddress:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if len(normalized) > 254 or not _EMAIL_PATTERN.match(normalized):
            raise InvalidEmail()
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TimeSlot:
    """Intervalo semiaberto [start, end): uma reunião pode começar quando a outra termina."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise InvalidTimeSlot("Os horários precisam informar o fuso horário.")
        object.__setattr__(self, "start", self.start.astimezone(UTC))
        object.__setattr__(self, "end", self.end.astimezone(UTC))

        if self.end <= self.start:
            raise InvalidTimeSlot("O término precisa ser depois do início.")
        if self.duration < MIN_DURATION:
            raise InvalidTimeSlot("A reserva precisa durar pelo menos 15 minutos.")
        if self.duration > MAX_DURATION:
            raise InvalidTimeSlot("A reserva pode durar no máximo 8 horas.")

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start < other.end and other.start < self.end
