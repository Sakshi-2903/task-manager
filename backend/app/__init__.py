"""Application factory.

`create_app` accepts an optional `db` so the Phase 2 test suite can inject a
mongomock database and run without a live MongoDB.
"""
import logging
import time

from flask import Flask, Response, request
from flask_cors import CORS
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, generate_latest
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

from .config import get_config
from .errors import register_error_handlers
from .fallback_db import FallbackDatabase

log = logging.getLogger(__name__)

REGISTRY = CollectorRegistry(auto_describe=True)
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)
REQUEST_LATENCY = Gauge(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    registry=REGISTRY,
)
ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Current active connections",
    registry=REGISTRY,
)


def create_app(config_object=None, db=None):
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    CORS(
        app,
        resources={
            r"/*": {"origins": app.config["CORS_ORIGINS"]},
        },
    )

    if db is not None:
        app.mongo_client = None
        app.db = db
        app.config["MONGO_AVAILABLE"] = False
    else:
        try:
            client = MongoClient(
                app.config["MONGO_URI"],
                serverSelectionTimeoutMS=app.config["MONGO_TIMEOUT_MS"],
                uuidRepresentation="standard",
            )
            database = client[app.config["MONGO_DB_NAME"]]
            database.command("ping")
            app.mongo_client = client
            app.db = database
            app.config["MONGO_AVAILABLE"] = True
        except Exception as exc:  # pragma: no cover - defensive fallback
            app.mongo_client = None
            app.db = FallbackDatabase()
            app.config["MONGO_AVAILABLE"] = False
            log.warning("Mongo initialization skipped: %s", exc)

    _ensure_indexes(app)
    register_error_handlers(app)

    @app.before_request
    def _before_request():
        app.config["_request_started_at"] = time.perf_counter()
        ACTIVE_CONNECTIONS.inc()

    @app.after_request
    def _after_request(response):
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status_code=response.status_code,
        ).inc()

        started_at = app.config.pop("_request_started_at", None)
        if started_at is not None:
            REQUEST_LATENCY.labels(method=request.method, endpoint=request.path).set(
                time.perf_counter() - started_at
            )
        ACTIVE_CONNECTIONS.dec()
        return response

    @app.route("/metrics")
    def metrics():
        payload = generate_latest(REGISTRY)
        return Response(payload, mimetype=CONTENT_TYPE_LATEST)

    from .routes.health import health_bp
    from .routes.tasks import tasks_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(tasks_bp)
    return app


def _ensure_indexes(app):
    """Best effort. Mongo being unreachable at boot must not crash the process,
    otherwise a database blip turns into a CrashLoopBackOff in Phase 5."""
    try:
        app.db.tasks.create_index([("status", ASCENDING)])
        app.db.tasks.create_index([("created_at", DESCENDING)])
    except PyMongoError as exc:
        log.warning("Index creation skipped: %s", exc)