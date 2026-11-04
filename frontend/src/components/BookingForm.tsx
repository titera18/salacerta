import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { api, type Room } from "../api";
import { addMinutes } from "../lib/time";
import { Modal } from "./Modal";

export interface BookingDraft {
  roomId: string;
  date: string;
  time: string;
}

interface BookingFormProps {
  rooms: Room[];
  draft: BookingDraft;
  onClose: () => void;
}

export function BookingForm({ rooms, draft, onClose }: BookingFormProps) {
  const queryClient = useQueryClient();
  const [roomId, setRoomId] = useState(draft.roomId);
  const [title, setTitle] = useState("");
  const [organizer, setOrganizer] = useState("");
  const [attendees, setAttendees] = useState(2);
  const [date, setDate] = useState(draft.date);
  const [start, setStart] = useState(draft.time);
  const [end, setEnd] = useState(addMinutes(draft.time, 60));

  const selectedRoom = rooms.find((room) => room.id === roomId);

  const mutation = useMutation({
    mutationFn: () =>
      api.scheduleBooking({
        room_id: roomId,
        title,
        organizer,
        attendees,
        start: new Date(`${date}T${start}`).toISOString(),
        end: new Date(`${date}T${end}`).toISOString(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      onClose();
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <Modal title="Nova reserva" onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <label>
          Título
          <input
            required
            maxLength={120}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Ex.: Planejamento da sprint"
          />
        </label>
        <label>
          Sala
          <select value={roomId} onChange={(event) => setRoomId(event.target.value)}>
            {rooms.map((room) => (
              <option key={room.id} value={room.id}>
                {room.name} · até {room.capacity} pessoas
              </option>
            ))}
          </select>
        </label>
        <div className="form-row three">
          <label>
            Data
            <input
              required
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
            />
          </label>
          <label>
            Início
            <input
              required
              type="time"
              value={start}
              onChange={(event) => {
                setStart(event.target.value);
                if (event.target.value) setEnd(addMinutes(event.target.value, 60));
              }}
            />
          </label>
          <label>
            Término
            <input
              required
              type="time"
              value={end}
              onChange={(event) => setEnd(event.target.value)}
            />
          </label>
        </div>
        <div className="form-row">
          <label>
            E-mail do organizador
            <input
              required
              type="email"
              value={organizer}
              onChange={(event) => setOrganizer(event.target.value)}
              placeholder="voce@empresa.com"
            />
          </label>
          <label>
            Participantes
            <input
              required
              type="number"
              min={1}
              max={selectedRoom?.capacity}
              value={attendees}
              onChange={(event) => setAttendees(Number(event.target.value))}
            />
          </label>
        </div>
        {mutation.error && (
          <p className="form-error" role="alert">
            {mutation.error.message}
          </p>
        )}
        <footer className="form-actions">
          <button type="button" className="button" onClick={onClose}>
            Voltar
          </button>
          <button type="submit" className="button primary" disabled={mutation.isPending}>
            {mutation.isPending ? "Reservando…" : "Reservar"}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
