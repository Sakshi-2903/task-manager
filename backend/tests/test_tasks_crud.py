import time

from bson import ObjectId

MISSING_ID = "507f1f77bcf86cd799439011"


def test_create_returns_201_with_defaults(client):
    response = client.post("/api/tasks", json={"title": "  write tests  "})
    assert response.status_code == 201

    body = response.get_json()
    assert body["title"] == "write tests"
    assert body["status"] == "todo"
    assert body["priority"] == "medium"
    assert body["description"] == ""
    assert body["due_date"] is None
    assert ObjectId.is_valid(body["id"])
    assert body["created_at"] == body["updated_at"]


def test_create_persists_the_document(client, db, make_task):
    created = make_task(title="persisted")
    stored = db.tasks.find_one({"_id": ObjectId(created["id"])})
    assert stored is not None
    assert stored["title"] == "persisted"


def test_create_never_leaks_raw_mongo_id(make_task):
    assert "_id" not in make_task()


def test_create_accepts_all_optional_fields(client):
    response = client.post(
        "/api/tasks",
        json={
            "title": "full task",
            "description": "with detail",
            "status": "in_progress",
            "priority": "low",
            "due_date": "2026-03-01T09:00:00Z",
        },
    )
    body = response.get_json()
    assert response.status_code == 201
    assert body["status"] == "in_progress"
    assert body["priority"] == "low"
    assert body["due_date"] == "2026-03-01T09:00:00Z"


def test_get_returns_the_task(client, make_task):
    created = make_task(title="fetch me")
    response = client.get(f"/api/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.get_json()["title"] == "fetch me"


def test_get_missing_task_returns_404(client):
    response = client.get(f"/api/tasks/{MISSING_ID}")
    assert response.status_code == 404
    assert response.get_json()["error"]["status"] == 404


def test_malformed_id_returns_400_not_500(client):
    """A bad ObjectId must not escape as an unhandled BSON error."""
    for method in (client.get, client.delete):
        assert method("/api/tasks/not-an-object-id").status_code == 400


def test_patch_updates_only_supplied_fields(client, make_task):
    created = make_task(title="original", description="keep me")
    response = client.patch(f"/api/tasks/{created['id']}", json={"status": "done"})
    body = response.get_json()

    assert response.status_code == 200
    assert body["status"] == "done"
    assert body["title"] == "original"
    assert body["description"] == "keep me"


def test_patch_bumps_updated_at(client, make_task):
    created = make_task()
    time.sleep(0.005)
    updated = client.patch(f"/api/tasks/{created['id']}", json={"title": "renamed"}).get_json()
    assert updated["updated_at"] > created["updated_at"]
    assert updated["created_at"] == created["created_at"]


def test_patch_can_clear_due_date(client, make_task):
    created = make_task(due_date="2026-03-01T09:00:00Z")
    updated = client.patch(f"/api/tasks/{created['id']}", json={"due_date": None}).get_json()
    assert updated["due_date"] is None


def test_patch_missing_task_returns_404(client):
    response = client.patch(f"/api/tasks/{MISSING_ID}", json={"status": "done"})
    assert response.status_code == 404


def test_delete_returns_204_and_removes_document(client, db, make_task):
    created = make_task()
    response = client.delete(f"/api/tasks/{created['id']}")
    assert response.status_code == 204
    assert response.data == b""
    assert db.tasks.count_documents({}) == 0


def test_delete_is_not_idempotent_second_call_404s(client, make_task):
    created = make_task()
    assert client.delete(f"/api/tasks/{created['id']}").status_code == 204
    assert client.delete(f"/api/tasks/{created['id']}").status_code == 404
