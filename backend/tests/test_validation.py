import pytest


def _errors(response):
    return response.get_json()["error"].get("details", {})


@pytest.mark.parametrize(
    "payload,field",
    [
        ({}, "title"),
        ({"title": ""}, "title"),
        ({"title": "   "}, "title"),
        ({"title": 123}, "title"),
        ({"title": "x" * 201}, "title"),
        ({"title": "ok", "description": 5}, "description"),
        ({"title": "ok", "description": "x" * 2001}, "description"),
        ({"title": "ok", "status": "archived"}, "status"),
        ({"title": "ok", "priority": "urgent"}, "priority"),
        ({"title": "ok", "due_date": "not-a-date"}, "due_date"),
        ({"title": "ok", "due_date": 1234}, "due_date"),
    ],
)
def test_create_rejects_bad_input(client, payload, field):
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 400
    assert field in _errors(response)


def test_all_field_errors_are_reported_at_once(client):
    """One round trip should surface every problem, not just the first."""
    response = client.post("/api/tasks", json={"title": "", "status": "bad", "priority": "bad"})
    assert set(_errors(response)) == {"title", "status", "priority"}


def test_error_response_has_a_consistent_shape(client):
    error = client.post("/api/tasks", json={}).get_json()["error"]
    assert set(error) >= {"message", "status"}
    assert error["status"] == 400


def test_non_object_body_is_rejected(client):
    assert client.post("/api/tasks", json=["not", "an", "object"]).status_code == 400


def test_invalid_json_body_returns_400(client):
    response = client.post("/api/tasks", data="{not json", content_type="application/json")
    assert response.status_code == 400


def test_missing_content_type_returns_400(client):
    assert client.post("/api/tasks", data="{}") .status_code == 400


def test_empty_patch_is_rejected(client, make_task):
    created = make_task()
    response = client.patch(f"/api/tasks/{created['id']}", json={})
    assert response.status_code == 400


def test_patch_rejects_invalid_values(client, make_task):
    created = make_task()
    response = client.patch(f"/api/tasks/{created['id']}", json={"status": "nope"})
    assert response.status_code == 400
    assert "status" in _errors(response)


def test_patch_ignores_unknown_fields(client, make_task):
    """Unknown keys must not be written into the document."""
    created = make_task()
    response = client.patch(
        f"/api/tasks/{created['id']}", json={"title": "renamed", "hacker": "value"}
    )
    assert response.status_code == 200
    assert "hacker" not in response.get_json()


def test_naive_due_date_is_treated_as_utc(client):
    response = client.post("/api/tasks", json={"title": "t", "due_date": "2026-03-01T09:00:00"})
    assert response.get_json()["due_date"] == "2026-03-01T09:00:00Z"


def test_unknown_route_returns_json_not_html(client):
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.is_json


def test_wrong_method_returns_json_405(client):
    response = client.put("/api/tasks")
    assert response.status_code == 405
    assert response.is_json
