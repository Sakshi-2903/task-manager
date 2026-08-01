"""Task document helpers: allowed values, id parsing, and serialisation."""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from ..errors import ApiError

STATUSES = ("todo", "in_progress", "done")
PRIORITIES = ("low", "medium", "high")

__all__ = ["STATUSES", "PRIORITIES", "utcnow", "to_object_id", "serialize"]


def utcnow():
    """Truncated to milliseconds: MongoDB stores BSON dates at millisecond
    precision, so keeping microseconds makes the POST response disagree with
    every subsequent GET of the same document."""
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


def to_object_id(value):
    """Turn a URL path segment into an ObjectId, or raise a clean 400."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ApiError(f"'{value}' is not a valid task id", 400)


def _iso(value):
    if value is None:
        return None
    if value.tzinfo is None:  # pymongo returns naive UTC datetimes
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def serialize(doc):
    """Mongo document -> JSON-safe dict. Never leak `_id` or raw BSON types."""
    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "description": doc.get("description", ""),
        "status": doc.get("status", "todo"),
        "priority": doc.get("priority", "medium"),
        "due_date": _iso(doc.get("due_date")),
        "created_at": _iso(doc.get("created_at")),
        "updated_at": _iso(doc.get("updated_at")),
    }