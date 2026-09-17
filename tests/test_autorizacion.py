import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user, get_gastos_repo
from app.models.usuario import Usuario


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# T6.4: Caso de error 4 de spec.md
def test_endpoints_gastos_sin_token_devuelven_401(client):
    # Asegurarse de que get_current_user NO esté sobreescrito
    app.dependency_overrides.pop(get_current_user, None)

    # GET /gastos/ sin header Authorization
    res_get = client.get("/gastos/")
    assert res_get.status_code == 401

    # POST /gastos/ sin header Authorization
    res_post = client.post(
        "/gastos/",
        json={"descripcion": "Almuerzo", "monto": 15.0, "categoria": "comida"},
    )
    assert res_post.status_code == 401


class RepositorioEspiaUsuario:
    def __init__(self):
        self.guardar_usuario_ids = []
        self.listar_usuario_ids = []

    def total_por_categoria(self, db, usuario_id, categoria):
        return 0.0

    def guardar(self, db, usuario_id: int, descripcion: str, monto: float, categoria: str) -> dict:
        self.guardar_usuario_ids.append(usuario_id)
        return {"id": 1, "descripcion": descripcion, "monto": monto, "categoria": categoria}

    def listar(self, db, usuario_id: int, skip: int = 0, limit: int = 20) -> list[dict]:
        self.listar_usuario_ids.append(usuario_id)
        if usuario_id == 1:
            return [{"id": 1, "descripcion": "Cena de A", "monto": 25.0, "categoria": "comida"}]
        return []


# T6.5: Caso de error 5 de spec.md
def test_usuario_id_ajeno_ignorado_en_body_y_query(client):
    usuario_a = Usuario(id=1, email="usuario_a@ejemplo.com", hashed_password="pwd")
    usuario_b_id = 999

    repo_espia = RepositorioEspiaUsuario()
    app.dependency_overrides[get_current_user] = lambda: usuario_a
    app.dependency_overrides[get_gastos_repo] = lambda: repo_espia

    # POST /gastos/ enviando usuario_id del usuario B en el body
    res_post = client.post(
        "/gastos/",
        json={
            "descripcion": "Cena de A",
            "monto": 25.0,
            "categoria": "comida",
            "usuario_id": usuario_b_id,
        },
    )
    assert res_post.status_code == 201
    # El repositorio recibió el usuario_id de A (1), no el de B (999)
    assert repo_espia.guardar_usuario_ids == [1]

    # GET /gastos/ pasando usuario_id ajeno como query param
    res_get = client.get(f"/gastos/?usuario_id={usuario_b_id}")
    # La respuesta NO debe ser 403, sino 200 ignorando el query param
    assert res_get.status_code == 200
    assert repo_espia.listar_usuario_ids == [1]
    data = res_get.json()
    assert len(data) == 1
    assert data[0]["descripcion"] == "Cena de A"
