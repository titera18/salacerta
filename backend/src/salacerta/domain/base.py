"""Blocos de construção táticos do DDD."""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Fato de negócio que já aconteceu; por isso é imutável."""


@dataclass(eq=False)
class AggregateRoot:
    """Entidade com identidade própria, responsável pela consistência do agregado."""

    id: UUID
    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False, kw_only=True)

    def __eq__(self, other: object) -> bool:
        return type(other) is type(self) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def _record(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events
