"""T8.3 — Las tools reutilizan services/ y resuelven la identidad correctamente.

Se usa monkeypatch (no unittest.mock) para sustituir SessionLocal y el contexto
de autenticación de MCP: el Artículo VII.2 prohíbe unittest.mock en estos tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.mcp.tools import gastos as tools_gastos
from app.repositories import usuarios as usuarios_repository


@pytest.fixture
def db_factory(monkeypatch):
    """Sustituye SessionLocal por una sesión contra SQLite en memoria."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    monkeypatch.setattr(tools_gastos, "SessionLocal", Session)
    yield Session
    Base.metadata.drop_all(engine)


class _TokenFalso:
    def __init__(self, subject):
        self.subject = subject


def _registrar(**kwargs):
    """Invoca la función registrar_gasto registrada como tool."""
    return _obtener_funciones()["registrar_gasto"](**kwargs)


def _listar(**kwargs):
    return _obtener_funciones()["listar_gastos"](**kwargs)


def _obtener_funciones():
    """register() define las tools como closures: se recuperan del FastMCP real."""
    from app.mcp.server import mcp

    return {
        nombre: mcp._tool_manager.get_tool(nombre).fn
        for nombre in ("registrar_gasto", "listar_gastos")
    }


def _sin_token(monkeypatch):
    monkeypatch.setattr(tools_gastos, "get_access_token", lambda: None)


def _con_token(monkeypatch, email):
    monkeypatch.setattr(tools_gastos, "get_access_token", lambda: _TokenFalso(email))


def test_registrar_gasto_exitoso_sin_token(db_factory, monkeypatch):
    """Sin token (stdio) se usa el usuario demo documentado — Artículo VI.4."""
    _sin_token(monkeypatch)
    resultado = _registrar(descripcion="Almuerzo", monto=12.50, categoria="comida")

    assert resultado["descripcion"] == "Almuerzo"
    assert resultado["monto"] == 12.50


def test_error_de_negocio_se_devuelve_estructurado(db_factory, monkeypatch):
    """Artículo VI.3: error claro, no una excepción sin controlar."""
    _sin_token(monkeypatch)
    resultado = _registrar(descripcion="Cine", monto=20.0, categoria="inventada")

    assert "error" in resultado
    assert "inventada" in resultado["error"]


def test_token_de_usuario_inexistente_no_cae_al_demo(db_factory, monkeypatch):
    """Artículo VI.4: con token, NUNCA se opera como usuario demo."""
    _con_token(monkeypatch, "fantasma@ejemplo.com")
    resultado = _registrar(descripcion="Intruso", monto=5.0, categoria="comida")

    assert "error" in resultado
    assert "no corresponde" in resultado["error"].lower()


def test_token_valido_opera_sobre_el_usuario_del_token(db_factory, monkeypatch):
    """Artículo VI.4: la identidad sale del token verificado, no del demo."""
    db = db_factory()
    usuarios_repository.guardar(db, "real@ejemplo.com", "hash-de-prueba")
    db.close()

    _con_token(monkeypatch, "real@ejemplo.com")
    _registrar(descripcion="Bus", monto=2.0, categoria="transporte")
    gastos = _listar()

    assert len(gastos) == 1
    assert gastos[0]["descripcion"] == "Bus"
