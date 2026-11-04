import logging
from collections.abc import Iterable
from datetime import UTC, datetime

from salacerta.domain.base import DomainEvent

logger = logging.getLogger("salacerta.events")


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class LoggingEventPublisher:
    """Registra os eventos em log. Trocar por uma fila não exige mudar os casos de uso."""

    def publish(self, events: Iterable[DomainEvent]) -> None:
        for event in events:
            logger.info("%s %s", type(event).__name__, event)
