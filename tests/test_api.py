"""Focused tests for the recruitment task's required behaviours."""

from fastapi.testclient import TestClient
import pytest

import database
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Give every test a fresh temporary SQLite database."""
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "test_registrations.db")
    database.initialize_database()
    with TestClient(app) as test_client:
        yield test_client


def registration_payload(email: str = "aisha@example.com") -> dict:
    return {
        "name": "Aisha Khan",
        "email": email,
        "college_department": "Computer Science",
    }


def test_student_can_register_and_be_retrieved(client):
    created = client.post("/register", json=registration_payload())

    assert created.status_code == 201
    body = created.json()
    assert body["message"] == "Registration successful."
    assert body["event"]["registered_count"] == 1
    assert body["event"]["remaining_seats"] == 49

    registration_id = body["registration"]["id"]
    found = client.get(f"/registrations/{registration_id}")
    assert found.status_code == 200
    assert found.json()["email"] == "aisha@example.com"


def test_duplicate_email_is_rejected_case_insensitively(client):
    client.post("/register", json=registration_payload())
    duplicate = client.post("/register", json=registration_payload("AISHA@EXAMPLE.COM"))

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "A registration already exists for this email address."


def test_missing_registration_returns_not_found(client):
    response = client.get("/registrations/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Registration not found."


def test_event_rejects_the_fifty_first_registration(client):
    for number in range(50):
        response = client.post(
            "/register",
            json=registration_payload(f"student{number}@example.com"),
        )
        assert response.status_code == 201

    full = client.post("/register", json=registration_payload("extra@example.com"))
    assert full.status_code == 409
    assert full.json()["detail"] == "Event is full. All 50 seats have been filled."
