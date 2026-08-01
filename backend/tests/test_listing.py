import pytest


@pytest.fixture
def seeded(make_task):
    return [
        make_task(title="alpha report", status="todo"),
        make_task(title="beta review", status="in_progress"),
        make_task(title="gamma Report", status="done"),
    ]


def test_list_returns_all_tasks_with_metadata(client, seeded):
    body = client.get("/api/tasks").get_json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["page"] == 1
    assert body["limit"] == 20


def test_list_is_newest_first(client, seeded):
    titles = [item["title"] for item in client.get("/api/tasks").get_json()["items"]]
    assert titles == ["gamma Report", "beta review", "alpha report"]


def test_empty_collection_returns_empty_list(client):
    body = client.get("/api/tasks").get_json()
    assert body == {"items": [], "page": 1, "limit": 20, "total": 0}


def test_status_filter(client, seeded):
    body = client.get("/api/tasks?status=done").get_json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "gamma Report"


def test_invalid_status_filter_returns_400(client):
    assert client.get("/api/tasks?status=archived").status_code == 400


def test_search_is_case_insensitive(client, seeded):
    body = client.get("/api/tasks?q=report").get_json()
    assert body["total"] == 2


def test_search_escapes_regex_metacharacters(client, make_task):
    """A '.' in the query must match a literal dot, not any character."""
    make_task(title="v1.0 release")
    make_task(title="v1x0 release")
    body = client.get("/api/tasks?q=v1.0").get_json()
    assert body["total"] == 1


def test_pagination_splits_results(client, seeded):
    first = client.get("/api/tasks?page=1&limit=2").get_json()
    second = client.get("/api/tasks?page=2&limit=2").get_json()

    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert second["total"] == 3
    assert first["items"][0]["id"] != second["items"][0]["id"]


def test_page_beyond_the_end_is_empty_but_reports_total(client, seeded):
    body = client.get("/api/tasks?page=99&limit=10").get_json()
    assert body["items"] == []
    assert body["total"] == 3


@pytest.mark.parametrize(
    "query",
    ["page=0", "page=-1", "limit=0", "limit=101", "page=abc", "limit=abc"],
)
def test_out_of_range_pagination_args_return_400(client, query):
    assert client.get(f"/api/tasks?{query}").status_code == 400


def test_limit_is_capped_at_the_documented_maximum(client):
    assert client.get("/api/tasks?limit=100").status_code == 200
    assert client.get("/api/tasks?limit=101").status_code == 400
