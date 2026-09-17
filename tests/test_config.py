import pytest
from pydantic import ValidationError
from app.config import Settings


def test_secret_key_es_obligatorio(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_defaults_de_configuracion():
    s = Settings(secret_key="clave-secreta-para-tests", _env_file=None)
    assert s.secret_key == "clave-secreta-para-tests"
    assert s.database_url == "sqlite:///./gastos.db"
    assert s.access_token_expire_minutes == 30
    assert s.log_level == "INFO"
    assert s.mcp_demo_email == "demo@curso.com"
    assert s.mcp_demo_password == "demo1234"
    assert s.mcp_issuer_url == "http://127.0.0.1:8000"
    assert s.mcp_resource_url == "http://127.0.0.1:8000/mcp"
