const MINUTES_PER_DAY = 24 * 60;

export const DEFAULT_WINDOW = { startHour: 7, endHour: 22 };

export interface HourWindow {
  startHour: number;
  endHour: number;
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function toDateInput(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function dayBounds(dateInput: string): { start: Date; end: Date } {
  const [year, month, day] = dateInput.split("-").map(Number);
  return { start: new Date(year, month - 1, day), end: new Date(year, month - 1, day + 1) };
}

export function shiftDate(dateInput: string, days: number): string {
  const { start } = dayBounds(dateInput);
  start.setDate(start.getDate() + days);
  return toDateInput(start);
}

/** Minutos desde o início do dia, limitados ao dia (reservas podem cruzar a meia-noite). */
export function minutesWithinDay(value: Date, dayStart: Date): number {
  const minutes = (value.getTime() - dayStart.getTime()) / 60_000;
  return Math.min(Math.max(minutes, 0), MINUTES_PER_DAY);
}

/** Amplia a janela padrão só quando alguma reserva cai fora dela. */
export function hourWindowFor(
  bookings: { start: string; end: string }[],
  dayStart: Date,
): HourWindow {
  let { startHour, endHour } = DEFAULT_WINDOW;
  for (const booking of bookings) {
    const first = minutesWithinDay(new Date(booking.start), dayStart);
    const last = minutesWithinDay(new Date(booking.end), dayStart);
    startHour = Math.min(startHour, Math.floor(first / 60));
    endHour = Math.max(endHour, Math.ceil(last / 60));
  }
  return { startHour, endHour };
}

/** Posição e largura, em porcentagem da faixa, de uma reserva na linha do tempo. */
export function blockPosition(
  start: Date,
  end: Date,
  dayStart: Date,
  window: HourWindow,
): { left: number; width: number } {
  const windowStart = window.startHour * 60;
  const total = (window.endHour - window.startHour) * 60;
  const from = minutesWithinDay(start, dayStart) - windowStart;
  const to = minutesWithinDay(end, dayStart) - windowStart;
  return { left: (from / total) * 100, width: ((to - from) / total) * 100 };
}

export type BlockDensity = "regular" | "compact" | "tiny";

/** Define quanto texto cabe no bloco: reservas curtas mostram menos e revelam o resto no hover. */
export function blockDensity(start: Date, end: Date): BlockDensity {
  const minutes = (end.getTime() - start.getTime()) / 60_000;
  if (minutes < 30) return "tiny";
  return minutes < 60 ? "compact" : "regular";
}

/** Converte a posição de um clique na faixa em horário, arredondado para baixo a cada 30 min. */
export function timeAtRatio(ratio: number, window: HourWindow): string {
  const total = (window.endHour - window.startHour) * 60;
  const minutes = window.startHour * 60 + Math.floor((ratio * total) / 30) * 30;
  const clamped = Math.min(minutes, window.endHour * 60 - 30);
  return `${pad(Math.floor(clamped / 60))}:${pad(clamped % 60)}`;
}

export function addMinutes(time: string, minutes: number): string {
  const [hours, mins] = time.split(":").map(Number);
  const total = Math.min(hours * 60 + mins + minutes, MINUTES_PER_DAY - 1);
  return `${pad(Math.floor(total / 60))}:${pad(total % 60)}`;
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

export function formatLongDate(dateInput: string): string {
  return dayBounds(dateInput).start.toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}
