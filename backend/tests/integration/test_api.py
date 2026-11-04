"""Exercita a pilha completa: HTTP, casos de uso, domínio e banco de verdade."""

from datetime import timedelta
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from tests.conftest import NOW, FixedClock, SpyPublisher


def create_room(client: TestClient, name: str = "Aurora", capacity: int = 10) -> dict[str, Any]:
    response = client.post("/api/rooms", json={"name": name, "capacity": capacity})
    assert response.status_code == 201, response.text
    return response.json()


def booking_payload(room_id: str, hours_ahead: float = 2, **overrides: Any) -> dict[str, Any]:
    start = NOW + timedelta(hours=hours_ahead)
    return {
        "room_id": room_id,
        "title": "Planejamento",
        "organizer": "ana@empresa.com",
        "attendees": 4,
        "start": start.isoformat(),
        "end": (start + timedelta(hours=1)).isoformat(),
        **overrides,
    }


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_list_rooms_sorted(client: TestClient) -> None:
    create_room(client, "Zênite")
    create_room(client, "Aurora")
    names = [room["name"] for room in client.get("/api/rooms").json()]
    assert names == ["Aurora", "Zênite"]


def test_duplicate_room_name_returns_409(client: TestClient) -> None:
    create_room(client)
    response = client.post("/api/rooms", json={"name": "aurora", "capacity": 4})
    assert response.status_code == 409
    assert response.json()["code"] == "room_name_taken"


def test_invalid_room_returns_422_with_domain_message(client: TestClient) -> None:
    response = client.post("/api/rooms", json={"name": "Aurora", "capacity": 0})
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_room"


def test_malformed_body_uses_same_error_format(client: TestClient) -> None:
    response = client.post("/api/rooms", json={"name": "Aurora", "capacity": "muitos"})
    assert response.status_code == 422
    assert response.json() == {
        "code": "invalid_request",
        "message": "Campo inválido: capacity.",
    }


def test_booking_lifecycle(client: TestClient, publisher: SpyPublisher) -> None:
    room = create_room(client)

    created = client.post("/api/bookings", json=booking_payload(room["id"]))
    assert created.status_code == 201
    booking = created.json()

    conflict = client.post("/api/bookings", json=booking_payload(room["id"], hours_ahead=2.5))
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "booking_conflict"

    assert client.post(f"/api/bookings/{booking['id']}/cancel").json()["status"] == "cancelled"
    assert client.post("/api/bookings", json=booking_payload(room["id"])).status_code == 201
    assert len(publisher.events) == 3


def test_adjacent_bookings_are_allowed(client: TestClient) -> None:
    room = create_room(client)
    assert client.post("/api/bookings", json=booking_payload(room["id"], 2)).status_code == 201
    assert client.post("/api/bookings", json=booking_payload(room["id"], 3)).status_code == 201


def test_same_time_in_different_rooms_is_allowed(client: TestClient) -> None:
    first, second = create_room(client, "Aurora"), create_room(client, "Zênite")
    assert client.post("/api/bookings", json=booking_payload(first["id"])).status_code == 201
    assert client.post("/api/bookings", json=booking_payload(second["id"])).status_code == 201


def test_capacity_and_unknown_room(client: TestClient) -> None:
    room = create_room(client, capacity=2)
    over = client.post("/api/bookings", json=booking_payload(room["id"], attendees=3))
    assert over.status_code == 422
    assert over.json()["code"] == "capacity_exceeded"

    missing = client.post("/api/bookings", json=booking_payload(str(uuid4())))
    assert missing.status_code == 404


def test_deactivated_room_refuses_bookings_until_reactivated(client: TestClient) -> None:
    room = create_room(client)
    assert client.post(f"/api/rooms/{room['id']}/deactivate").json()["is_active"] is False

    refused = client.post("/api/bookings", json=booking_payload(room["id"]))
    assert refused.json()["code"] == "room_inactive"

    assert client.post(f"/api/rooms/{room['id']}/activate").json()["is_active"] is True
    assert client.post("/api/bookings", json=booking_payload(room["id"])).status_code == 201


def test_datetime_without_timezone_is_rejected(client: TestClient) -> None:
    room = create_room(client)
    payload = booking_payload(room["id"], start="2030-01-07T14:00:00", end="2030-01-07T15:00:00")
    assert client.post("/api/bookings", json=payload).status_code == 422


def test_list_returns_only_active_bookings_in_period_as_utc(client: TestClient) -> None:
    room = create_room(client)
    inside = client.post("/api/bookings", json=booking_payload(room["id"], 2)).json()
    cancelled = client.post("/api/bookings", json=booking_payload(room["id"], 4)).json()
    client.post("/api/bookings", json=booking_payload(room["id"], 48))
    client.post(f"/api/bookings/{cancelled['id']}/cancel")

    response = client.get(
        "/api/bookings",
        params={
            "start": NOW.isoformat(),
            "end": (NOW + timedelta(hours=24)).isoformat(),
            "room_id": room["id"],
        },
    )

    assert [item["id"] for item in response.json()] == [inside["id"]]
    assert response.json()[0]["start"] in ("2030-01-07T14:00:00Z", "2030-01-07T14:00:00+00:00")


def test_cannot_cancel_started_booking(client: TestClient, clock: FixedClock) -> None:
    room = create_room(client)
    booking = client.post("/api/bookings", json=booking_payload(room["id"])).json()

    clock.current = NOW + timedelta(hours=3)

    response = client.post(f"/api/bookings/{booking['id']}/cancel")
    assert response.status_code == 422
    assert response.json()["code"] == "booking_not_cancellable"
