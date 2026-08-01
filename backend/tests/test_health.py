import app as app_module
from pymongo.errors import PyMongoError

from app import create_app
from app.config import TestingConfig


def test_liveness_is_always_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readiness_ok_when_database_responds(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"


class _BrokenCollection:
    def create_index(self, *_args, **_kwargs):
        raise PyMongoError("connection refused")


class _BrokenDb:
    """Stands in for a database that cannot be reached."""

    tasks = _BrokenCollection()

    def command(self, *_args, **_kwargs):
        raise PyMongoError("connection refused")


def test_readiness_returns_ready_with_fallback_when_database_is_down():
    app = create_app(TestingConfig, db=_BrokenDb())
    response = app.test_client().get("/readyz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"


def test_app_starts_even_if_index_creation_fails():
    """Mongo down at boot must not crash the process, or Phase 5 turns a
    database blip into a CrashLoopBackOff."""
    app = create_app(TestingConfig, db=_BrokenDb())
    assert app.test_client().get("/healthz").status_code == 200


def test_liveness_still_ok_when_database_is_down():
    """The whole point of splitting the probes: a Mongo outage must not
    trigger pod restarts in Phase 5."""
    app = create_app(TestingConfig, db=_BrokenDb())
    assert app.test_client().get("/healthz").status_code == 200


def test_app_uses_fallback_db_when_mongo_initialization_fails(monkeypatch):
    """A Mongo connection failure should leave the app usable and marked as
    degraded rather than crash the process."""

    class _InitError(Exception):
        pass

    def _raise(*_args, **_kwargs):
        raise _InitError("boom")

    monkeypatch.setattr(app_module, "MongoClient", _raise)
    app = create_app(TestingConfig)

    assert app.test_client().get("/healthz").status_code == 200
    assert app.config["MONGO_AVAILABLE"] is False