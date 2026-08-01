"""Configuration objects. Every value comes from the environment so the same
image can run locally, in CI, and in Kubernetes with no code changes."""
import os


def _origins():
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


class BaseConfig:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "taskmanager")
    MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "3000"))
    CORS_ORIGINS = _origins()
    DEBUG = False
    TESTING = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    MONGO_DB_NAME = "taskmanager_test"


class ProductionConfig(BaseConfig):
    pass


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = name or os.getenv("FLASK_ENV", "development")
    return _CONFIGS.get(name, DevelopmentConfig)
