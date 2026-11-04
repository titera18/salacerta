"""Erros do domínio. A interface HTTP traduz cada categoria para um status."""


class DomainError(Exception):
    code = "domain_error"
    message = "Operação inválida."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class RuleViolation(DomainError):
    """Uma regra de negócio impediu a operação."""


class NotFound(DomainError):
    """O agregado solicitado não existe."""


class Conflict(DomainError):
    """A operação colide com o estado atual do sistema."""


class InvalidRoom(RuleViolation):
    code = "invalid_room"


class InvalidTimeSlot(RuleViolation):
    code = "invalid_time_slot"


class InvalidEmail(RuleViolation):
    code = "invalid_email"
    message = "Informe um e-mail válido."


class InvalidBooking(RuleViolation):
    code = "invalid_booking"


class RoomInactive(RuleViolation):
    code = "room_inactive"
    message = "Esta sala está desativada e não aceita novas reservas."


class CapacityExceeded(RuleViolation):
    code = "capacity_exceeded"


class BookingInPast(RuleViolation):
    code = "booking_in_past"
    message = "A reserva precisa começar no futuro."


class BookingNotCancellable(RuleViolation):
    code = "booking_not_cancellable"


class RoomNotFound(NotFound):
    code = "room_not_found"
    message = "Sala não encontrada."


class BookingNotFound(NotFound):
    code = "booking_not_found"
    message = "Reserva não encontrada."


class RoomNameTaken(Conflict):
    code = "room_name_taken"
    message = "Já existe uma sala com este nome."


class BookingConflict(Conflict):
    code = "booking_conflict"
    message = "A sala já está reservada neste horário."
