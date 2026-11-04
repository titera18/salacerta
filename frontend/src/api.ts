export interface Room {
  id: string;
  name: string;
  capacity: number;
  is_active: boolean;
}

export interface Booking {
  id: string;
  room_id: string;
  title: string;
  organizer: string;
  attendees: number;
  start: string;
  end: string;
  status: "scheduled" | "cancelled";
}

export interface NewBooking {
  room_id: string;
  title: string;
  organizer: string;
  attendees: number;
  start: string;
  end: string;
}

export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...init,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    throw new ApiError("network_error", "Não foi possível falar com o servidor.");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      body?.code ?? "unexpected_error",
      body?.message ?? "Algo deu errado. Tente novamente.",
    );
  }
  return response.json() as Promise<T>;
}

export const api = {
  listRooms: () => request<Room[]>("/rooms"),

  createRoom: (name: string, capacity: number) =>
    request<Room>("/rooms", {
      method: "POST",
      body: JSON.stringify({ name, capacity }),
    }),

  setRoomActive: (roomId: string, active: boolean) =>
    request<Room>(`/rooms/${roomId}/${active ? "activate" : "deactivate"}`, {
      method: "POST",
    }),

  listBookings: (start: Date, end: Date) => {
    const params = new URLSearchParams({
      start: start.toISOString(),
      end: end.toISOString(),
    });
    return request<Booking[]>(`/bookings?${params}`);
  },

  scheduleBooking: (booking: NewBooking) =>
    request<Booking>("/bookings", {
      method: "POST",
      body: JSON.stringify(booking),
    }),

  cancelBooking: (bookingId: string) =>
    request<Booking>(`/bookings/${bookingId}/cancel`, { method: "POST" }),
};
