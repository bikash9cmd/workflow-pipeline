"""
Couple of sanity tests for the booking flow. Not trying to cover every edge
case here, mainly checking the stuff that would actually be embarrassing to
get wrong (booking in the past, double-cancelling).

Run with: pytest tests/
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "session-backend"))

from app import app, db  # noqa: E402
from models import Client, Session  # noqa: E402


@pytest.fixture
def client():
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_cant_book_in_the_past(client):
    resp = client.post("/sessions/book", json={
        "name": "Test Client",
        "email": "test@example.com",
        "scheduled_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
    })
    assert resp.status_code == 400


def test_book_then_cancel(client):
    resp = client.post("/sessions/book", json={
        "name": "Test Client",
        "email": "test@example.com",
        "scheduled_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
    })
    assert resp.status_code == 201
    session_id = resp.get_json()["id"]

    cancel_resp = client.post(f"/sessions/{session_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.get_json()["status"] == "cancelled"

    # cancelling again should be rejected, not silently succeed
    second_cancel = client.post(f"/sessions/{session_id}/cancel")
    assert second_cancel.status_code == 400
