"""T8.4 — MCP montado en FastAPI exige token, y REST sigue funcionando igual.

No se entra al lifespan aquí (sin `with`): el corte por autenticación ocurre en
RequireAuthMiddleware, antes del session manager de streamable-http. Entrar al
lifespan en dos archivos distintos rompe con RuntimeError, porque
session_manager.run() solo admite una llamada por instancia.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

CABECERAS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


@pytest.fixture(scope="module")
def client():
    # base_url con host real: el SDK de MCP rechaza "testserver" con 421 por
    # su protección contra DNS rebinding.
    return TestClient(app, base_url="http://127.0.0.1:8000")


def test_mcp_sin_token_devuelve_401(client):
    """Artículo VI.4: el corte ocurre en el middleware, antes de ejecutar una tool."""
    response = client.post("/mcp/", headers=CABECERAS, json={})

    assert response.status_code == 401
    assert "www-authenticate" in response.headers


def test_rest_sigue_respondiendo_en_el_mismo_proceso(client):
    """Montar MCP no altera los endpoints REST de la Sesión 7."""
    response = client.get("/gastos/")

    assert response.status_code == 401
