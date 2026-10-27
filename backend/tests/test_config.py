from app.core.config import get_settings


def test_default_config_loads() -> None:
    settings = get_settings()
    assert settings.app.api_prefix == "/api/v1"
    assert settings.redis.url.startswith("redis://")
    assert settings.qdrant.collection == "kb_default"
