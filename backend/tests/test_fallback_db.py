from app import create_app


class DummyConfig:
    MONGO_URI = "mongodb://127.0.0.1:1"
    MONGO_DB_NAME = "taskmanager_test"
    MONGO_TIMEOUT_MS = 1
    CORS_ORIGINS = ["http://localhost:5173"]
    DEBUG = False
    TESTING = False


def test_api_returns_empty_list_when_mongo_is_unavailable():
    app = create_app(config_object=DummyConfig)
    client = app.test_client()

    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.get_json() == {
        "items": [],
        "page": 1,
        "limit": 20,
        "total": 0,
    }
