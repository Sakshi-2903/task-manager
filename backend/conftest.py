from datetime import datetime, timedelta, timezone

import mongomock
import pytest

from app import create_app
from app.config import TestingConfig


@pytest.fixture
def db():
    return mongomock.MongoClient()["taskmanager_test"]


@pytest.fixture
def app(db):
    return create_app(TestingConfig, db=db)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_task(client):
    def _make(**overrides):
        payload = {"title": "sample task"}
        payload.update(overrides)

        if "created_at" not in payload:
            payload["created_at"] = datetime.now(timezone.utc).isoformat()

        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 201, response.get_json()
        return response.get_json()

    return _make
