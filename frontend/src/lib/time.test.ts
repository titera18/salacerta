import { describe, expect, it } from "vitest";
import {
  addMinutes,
  blockDensity,
  blockPosition,
  dayBounds,
  hourWindowFor,
  shiftDate,
  timeAtRatio,
} from "./time";

const day = dayBounds("2030-01-07").start;
const at = (hour: number, minute = 0, date = 7) => new Date(2030, 0, date, hour, minute);

describe("shiftDate", () => {
  it("atravessa a virada do mês", () => {
    expect(shiftDate("2030-01-31", 1)).toBe("2030-02-01");
    expect(shiftDate("2030-03-01", -1)).toBe("2030-02-28");
  });
});

describe("hourWindowFor", () => {
  it("mantém a janela padrão quando as reservas cabem nela", () => {
    const bookings = [{ start: at(9).toISOString(), end: at(10).toISOString() }];
    expect(hourWindowFor(bookings, day)).toEqual({ startHour: 7, endHour: 22 });
  });

  it("amplia a janela para mostrar reservas fora do horário", () => {
    const bookings = [
      { start: at(5, 30).toISOString(), end: at(6).toISOString() },
      { start: at(22).toISOString(), end: at(23, 15).toISOString() },
    ];
    expect(hourWindowFor(bookings, day)).toEqual({ startHour: 5, endHour: 24 });
  });
});

describe("blockPosition", () => {
  const window = { startHour: 8, endHour: 18 };

  it("calcula a posição proporcional", () => {
    expect(blockPosition(at(9), at(10), day, window)).toEqual({ left: 10, width: 10 });
  });

  it("corta na meia-noite uma reserva que continua no dia seguinte", () => {
    const full = { startHour: 0, endHour: 24 };
    const { left, width } = blockPosition(at(23), at(1, 0, 8), day, full);
    expect(left + width).toBeCloseTo(100);
  });
});

describe("blockDensity", () => {
  it("reduz o conteúdo conforme a duração", () => {
    expect(blockDensity(at(9), at(9, 15))).toBe("tiny");
    expect(blockDensity(at(9), at(9, 30))).toBe("compact");
    expect(blockDensity(at(9), at(10))).toBe("regular");
  });
});

describe("timeAtRatio", () => {
  const window = { startHour: 8, endHour: 18 };

  it("arredonda para o intervalo de 30 minutos", () => {
    expect(timeAtRatio(0, window)).toBe("08:00");
    expect(timeAtRatio(0.13, window)).toBe("09:00");
    expect(timeAtRatio(0.16, window)).toBe("09:30");
  });

  it("não ultrapassa o fim da janela", () => {
    expect(timeAtRatio(1, window)).toBe("17:30");
  });
});

describe("addMinutes", () => {
  it("soma minutos e não passa do fim do dia", () => {
    expect(addMinutes("09:30", 60)).toBe("10:30");
    expect(addMinutes("23:30", 60)).toBe("23:59");
  });
});
