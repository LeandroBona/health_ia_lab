from app.core.config import _cors_origin_regex, _cors_origins


def test_explicit_empty_cors_disables_development_origins(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "")
    assert _cors_origins() == []
    assert _cors_origin_regex() is None
