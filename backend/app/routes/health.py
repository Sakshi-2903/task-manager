"""Liveness and readiness probes.

The distinction matters for Phase 5: liveness answering 200 means "the process
is healthy, do not restart me". Readiness answering 503 means "I cannot serve
traffic right now" and pulls the pod out of the Service endpoints instead of
killing it. Checking Mongo in the liveness probe would cause a restart storm
every time the database hiccups.
"""
from flask import Blueprint, current_app, jsonify
from pymongo.errors import PyMongoError

from app.fallback_db import FallbackDatabase

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@health_bp.get("/healthz")
def liveness():
    return jsonify({"status": "ok"})


@health_bp.get("/health/ready")
@health_bp.get("/readyz")
def readiness():
    db = getattr(current_app, "db", None)
    if db is None:
        return jsonify({"status": "unavailable", "detail": "database not initialized"}), 503

    if getattr(current_app.config, "get", lambda *_: False)("MONGO_AVAILABLE", True) is False:
        return jsonify({"status": "ready", "detail": "using fallback in-memory database"})

    try:
        db.command("ping")
    except PyMongoError:
        current_app.config["MONGO_AVAILABLE"] = False
        current_app.db = FallbackDatabase()
        return jsonify({"status": "ready", "detail": "using fallback in-memory database"})
    return jsonify({"status": "ready"})