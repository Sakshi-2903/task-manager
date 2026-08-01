"""Hand-rolled validation. Collects *all* field errors before raising so the
client gets one useful 400 instead of a game of whack-a-mole."""
from datetime import datetime, timezone

from .errors import ApiError
from .models.task import PRIORITIES, STATUSES, utcnow

MAX_TITLE = 200
MAX_DESCRIPTION = 2000


def _parse_due_date(raw, errors):
    if raw is None:
        return None
    if not isinstance(raw, str):
        errors["due_date"] = "must be an ISO-8601 string, e.g. 2026-03-01T09:00:00Z"
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        errors["due_date"] = "must be an ISO-8601 string, e.g. 2026-03-01T09:00:00Z"
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _check_title(value, errors):
    if not isinstance(value, str) or not value.strip():
        errors["title"] = "required, must be a non-empty string"
        return None
    cleaned = value.strip()
    if len(cleaned) > MAX_TITLE:
        errors["title"] = f"must be at most {MAX_TITLE} characters"
        return None
    return cleaned


def _check_description(value, errors):
    if value is None:
        return ""
    if not isinstance(value, str):
        errors["description"] = "must be a string"
        return None
    if len(value) > MAX_DESCRIPTION:
        errors["description"] = f"must be at most {MAX_DESCRIPTION} characters"
        return None
    return value


def _check_choice(field, value, allowed, errors):
    if value not in allowed:
        errors[field] = f"must be one of: {', '.join(allowed)}"
        return None
    return value


def _require_object(payload):
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object", 400)


def validate_create(payload):
    """Return a ready-to-insert Mongo document."""
    _require_object(payload)
    errors = {}

    title = _check_title(payload.get("title"), errors)
    description = _check_description(payload.get("description"), errors)
    status = _check_choice("status", payload.get("status", "todo"), STATUSES, errors)
    priority = _check_choice("priority", payload.get("priority", "medium"), PRIORITIES, errors)
    due_date = _parse_due_date(payload.get("due_date"), errors)

    if errors:
        raise ApiError("Validation failed", 400, errors)

    now = utcnow()
    return {
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "due_date": due_date,
        "created_at": now,
        "updated_at": now,
    }


def validate_update(payload):
    """Return a partial `$set` document. Only supplied fields are touched."""
    _require_object(payload)
    errors = {}
    changes = {}

    if "title" in payload:
        changes["title"] = _check_title(payload["title"], errors)
    if "description" in payload:
        changes["description"] = _check_description(payload["description"], errors)
    if "status" in payload:
        changes["status"] = _check_choice("status", payload["status"], STATUSES, errors)
    if "priority" in payload:
        changes["priority"] = _check_choice("priority", payload["priority"], PRIORITIES, errors)
    if "due_date" in payload:
        changes["due_date"] = _parse_due_date(payload["due_date"], errors)

    if errors:
        raise ApiError("Validation failed", 400, errors)
    if not changes:
        raise ApiError("No updatable fields supplied", 400)

    changes["updated_at"] = utcnow()
    return changes
