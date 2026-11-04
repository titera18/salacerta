import { type MouseEvent } from "react";
import type { Booking, Room } from "../api";
import {
  blockDensity,
  blockPosition,
  formatTime,
  type HourWindow,
  hourWindowFor,
  timeAtRatio,
} from "../lib/time";

interface TimelineProps {
  rooms: Room[];
  bookings: Booking[];
  dayStart: Date;
  onSelectSlot: (roomId: string, time: string) => void;
  onSelectBooking: (booking: Booking) => void;
  onToggleRoom: (room: Room) => void;
}

export function Timeline({
  rooms,
  bookings,
  dayStart,
  onSelectSlot,
  onSelectBooking,
  onToggleRoom,
}: TimelineProps) {
  const window = hourWindowFor(bookings, dayStart);
  const hours = Array.from(
    { length: window.endHour - window.startHour },
    (_, index) => window.startHour + index,
  );

  return (
    <div className="timeline-scroll">
      <div className="timeline" style={{ "--hours": hours.length } as React.CSSProperties}>
        <div className="timeline-row timeline-head">
          <div className="room-cell" />
          <div className="hours">
            {hours.map((hour) => (
              <span key={hour}>{String(hour).padStart(2, "0")}h</span>
            ))}
          </div>
        </div>
        {rooms.map((room) => (
          <TimelineRow
            key={room.id}
            room={room}
            bookings={bookings.filter((booking) => booking.room_id === room.id)}
            dayStart={dayStart}
            window={window}
            onSelectSlot={onSelectSlot}
            onSelectBooking={onSelectBooking}
            onToggleRoom={onToggleRoom}
          />
        ))}
      </div>
    </div>
  );
}

interface TimelineRowProps extends Omit<TimelineProps, "rooms"> {
  room: Room;
  window: HourWindow;
}

function TimelineRow({
  room,
  bookings,
  dayStart,
  window,
  onSelectSlot,
  onSelectBooking,
  onToggleRoom,
}: TimelineRowProps) {
  function handleTrackClick(event: MouseEvent<HTMLDivElement>) {
    if (!room.is_active) return;
    const rect = event.currentTarget.getBoundingClientRect();
    onSelectSlot(room.id, timeAtRatio((event.clientX - rect.left) / rect.width, window));
  }

  return (
    <div className={`timeline-row${room.is_active ? "" : " inactive"}`}>
      <div className="room-cell">
        <strong title={room.name}>{room.name}</strong>
        <span className="room-meta">
          {room.is_active ? `até ${room.capacity} pessoas` : "Desativada"}
          {" · "}
          <button type="button" className="link-button" onClick={() => onToggleRoom(room)}>
            {room.is_active ? "desativar" : "reativar"}
          </button>
        </span>
      </div>
      <div
        className="track"
        onClick={handleTrackClick}
        title={room.is_active ? "Clique para reservar" : undefined}
      >
        {bookings.map((booking) => {
          const { left, width } = blockPosition(
            new Date(booking.start),
            new Date(booking.end),
            dayStart,
            window,
          );
          return (
            <button
              key={booking.id}
              type="button"
              className={`block ${blockDensity(new Date(booking.start), new Date(booking.end))}`}
              style={{ left: `${left}%`, width: `${width}%` }}
              title={`${booking.title} · ${formatTime(booking.start)}–${formatTime(booking.end)}`}
              onClick={(event) => {
                event.stopPropagation();
                onSelectBooking(booking);
              }}
            >
              <span className="block-title">{booking.title}</span>
              <span className="block-time">
                {formatTime(booking.start)}–{formatTime(booking.end)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
