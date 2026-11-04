import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api, type Booking, type Room } from "./api";
import { BookingDetails } from "./components/BookingDetails";
import { BookingForm, type BookingDraft } from "./components/BookingForm";
import { RoomForm } from "./components/RoomForm";
import { Timeline } from "./components/Timeline";
import { dayBounds, formatLongDate, shiftDate, toDateInput } from "./lib/time";

export function App() {
  const queryClient = useQueryClient();
  const today = toDateInput(new Date());
  const [date, setDate] = useState(today);
  const [creatingRoom, setCreatingRoom] = useState(false);
  const [draft, setDraft] = useState<BookingDraft | null>(null);
  const [selected, setSelected] = useState<Booking | null>(null);

  const { start: dayStart, end: dayEnd } = useMemo(() => dayBounds(date), [date]);

  const rooms = useQuery({ queryKey: ["rooms"], queryFn: api.listRooms });
  const bookings = useQuery({
    queryKey: ["bookings", date],
    queryFn: () => api.listBookings(dayStart, dayEnd),
  });

  const toggleRoom = useMutation({
    mutationFn: (room: Room) => api.setRoomActive(room.id, !room.is_active),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["rooms"] }),
  });

  const allRooms = rooms.data ?? [];
  const activeRooms = allRooms.filter((room) => room.is_active);
  const loadError = rooms.error ?? bookings.error;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            ✓
          </span>
          SalaCerta
        </div>
        <div className="topbar-actions">
          <button type="button" className="button" onClick={() => setCreatingRoom(true)}>
            Nova sala
          </button>
          <button
            type="button"
            className="button primary"
            disabled={activeRooms.length === 0}
            onClick={() => setDraft({ roomId: activeRooms[0].id, date, time: "09:00" })}
          >
            Nova reserva
          </button>
        </div>
      </header>

      <main className="content">
        <div className="day-nav">
          <h1>{formatLongDate(date)}</h1>
          <div className="day-controls">
            <button
              type="button"
              className="button"
              aria-label="Dia anterior"
              onClick={() => setDate(shiftDate(date, -1))}
            >
              ‹
            </button>
            <button
              type="button"
              className="button"
              disabled={date === today}
              onClick={() => setDate(today)}
            >
              Hoje
            </button>
            <button
              type="button"
              className="button"
              aria-label="Próximo dia"
              onClick={() => setDate(shiftDate(date, 1))}
            >
              ›
            </button>
            <input
              type="date"
              aria-label="Escolher data"
              value={date}
              onChange={(event) => event.target.value && setDate(event.target.value)}
            />
          </div>
        </div>

        {loadError && (
          <p className="banner-error" role="alert">
            {loadError.message}
          </p>
        )}
        {toggleRoom.error && (
          <p className="banner-error" role="alert">
            {toggleRoom.error.message}
          </p>
        )}

        {rooms.isPending ? (
          <p className="muted">Carregando…</p>
        ) : allRooms.length === 0 && !rooms.error ? (
          <section className="empty">
            <h2>Nenhuma sala cadastrada</h2>
            <p>Cadastre a primeira sala para começar a receber reservas.</p>
            <button type="button" className="button primary" onClick={() => setCreatingRoom(true)}>
              Cadastrar sala
            </button>
          </section>
        ) : (
          allRooms.length > 0 && (
            <Timeline
              rooms={allRooms}
              bookings={bookings.data ?? []}
              dayStart={dayStart}
              onSelectSlot={(roomId, time) => setDraft({ roomId, date, time })}
              onSelectBooking={setSelected}
              onToggleRoom={(room) => toggleRoom.mutate(room)}
            />
          )
        )}
      </main>

      {creatingRoom && <RoomForm onClose={() => setCreatingRoom(false)} />}
      {draft && <BookingForm rooms={activeRooms} draft={draft} onClose={() => setDraft(null)} />}
      {selected && (
        <BookingDetails
          booking={selected}
          room={allRooms.find((room) => room.id === selected.room_id)}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
