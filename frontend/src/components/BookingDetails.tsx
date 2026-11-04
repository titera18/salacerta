import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type Booking, type Room } from "../api";
import { formatTime } from "../lib/time";
import { Modal } from "./Modal";

interface BookingDetailsProps {
  booking: Booking;
  room: Room | undefined;
  onClose: () => void;
}

export function BookingDetails({ booking, room, onClose }: BookingDetailsProps) {
  const queryClient = useQueryClient();
  const started = new Date(booking.start).getTime() <= Date.now();

  const mutation = useMutation({
    mutationFn: () => api.cancelBooking(booking.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      onClose();
    },
  });

  return (
    <Modal title={booking.title} onClose={onClose}>
      <dl className="details">
        <dt>Sala</dt>
        <dd>{room?.name ?? "—"}</dd>
        <dt>Horário</dt>
        <dd>
          {new Date(booking.start).toLocaleDateString("pt-BR")}, {formatTime(booking.start)} às{" "}
          {formatTime(booking.end)}
        </dd>
        <dt>Organizador</dt>
        <dd>{booking.organizer}</dd>
        <dt>Participantes</dt>
        <dd>{booking.attendees}</dd>
      </dl>
      {mutation.error && (
        <p className="form-error" role="alert">
          {mutation.error.message}
        </p>
      )}
      <footer className="form-actions">
        <button type="button" className="button" onClick={onClose}>
          Voltar
        </button>
        {!started && (
          <button
            type="button"
            className="button danger"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? "Cancelando…" : "Cancelar reserva"}
          </button>
        )}
      </footer>
    </Modal>
  );
}
