import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.dependencies import get_current_user, get_gastos_repo
from app.models.usuario import Usuario
from app.routers.gastos import router
from tests.test_gastos import RepositorioFalso

USUARIO_TEST = Usuario(id=1, email="test@ejemplo.com", hashed_password="pwd")


@pytest.fixture
def client_gastos():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: USUARIO_TEST

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_post_gasto_categoria_invalida_400(client_gastos):
    client_gastos.app.dependency_overrides[get_gastos_repo] = lambda: RepositorioFalso()
    response = client_gastos.post(
        "/gastos/",
        json={"descripcion": "Almuerzo", "monto": 20.0, "categoria": "categoria_falsa"},
    )
    assert response.status_code == 400
    assert "no es una categoría válida" in response.json()["detail"]


def test_post_gasto_excede_limite_400(client_gastos):
    client_gastos.app.dependency_overrides[get_gastos_repo] = lambda: RepositorioFalso(
        total_inicial_por_categoria=490.0
    )
    response = client_gastos.post(
        "/gastos/",
        json={"descripcion": "Cena cara", "monto": 50.0, "categoria": "comida"},
    )
    assert response.status_code == 400
    assert "supera el límite" in response.json()["detail"]


def test_post_gasto_monto_invalido_400(client_gastos):
    client_gastos.app.dependency_overrides[get_gastos_repo] = lambda: RepositorioFalso()
    response = client_gastos.post(
        "/gastos/",
        json={"descripcion": "Café", "monto": -5.0, "categoria": "comida"},
    )
    assert response.status_code == 400
    assert "mayor a cero" in response.json()["detail"]
