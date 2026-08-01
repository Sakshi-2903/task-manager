"""CRUD endpoints for /api/tasks."""
import re

from flask import Blueprint, current_app, jsonify, request
from pymongo import ReturnDocument

from ..errors import ApiError
from ..models.task import STATUSES, serialize, to_object_id
from ..schemas import validate_create, validate_update

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _tasks():
    return current_app.db.tasks


def _int_arg(name, default, minimum, maximum=None):
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(f"'{name}' must be an integer", 400)
    if value < minimum or (maximum is not None and value > maximum):
        bound = f"between {minimum} and {maximum}" if maximum else f"at least {minimum}"
        raise ApiError(f"'{name}' must be {bound}", 400)
    return value


def _body():
    payload = request.get_json(silent=True)
    if payload is None:
        raise ApiError("Request body must be valid JSON", 400)
    return payload


@tasks_bp.get("/tasks")
def list_tasks():
    query = {}

    status = request.args.get("status")
    if status:
        if status not in STATUSES:
            raise ApiError(f"'status' must be one of: {', '.join(STATUSES)}", 400)
        query["status"] = status

    search = request.args.get("q")
    if search:
        query["title"] = {"$regex": re.escape(search), "$options": "i"}

    page = _int_arg("page", 1, minimum=1)
    limit = _int_arg("limit", DEFAULT_LIMIT, minimum=1, maximum=MAX_LIMIT)

    cursor = (
        _tasks()
        .find(query)
        .sort([("created_at", -1), ("_id", -1)])
        .skip((page - 1) * limit)
        .limit(limit)
    )
    return jsonify({
        "items": [serialize(doc) for doc in cursor],
        "page": page,
        "limit": limit,
        "total": _tasks().count_documents(query),
    })


@tasks_bp.post("/tasks")
def create_task():
    document = validate_create(_body())
    result = _tasks().insert_one(document)
    document["_id"] = result.inserted_id
    return jsonify(serialize(document)), 201


@tasks_bp.get("/tasks/<task_id>")
def get_task(task_id):
    doc = _tasks().find_one({"_id": to_object_id(task_id)})
    if doc is None:
        raise ApiError("Task not found", 404)
    return jsonify(serialize(doc))


@tasks_bp.patch("/tasks/<task_id>")
def update_task(task_id):
    changes = validate_update(_body())
    doc = _tasks().find_one_and_update(
        {"_id": to_object_id(task_id)},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        raise ApiError("Task not found", 404)
    return jsonify(serialize(doc))


@tasks_bp.delete("/tasks/<task_id>")
def delete_task(task_id):
    result = _tasks().delete_one({"_id": to_object_id(task_id)})
    if result.deleted_count == 0:
        raise ApiError("Task not found", 404)
    return "", 204