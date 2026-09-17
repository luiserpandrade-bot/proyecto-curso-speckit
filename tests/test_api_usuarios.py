import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.routers.usuarios import router


@pytest.fixture
def client_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_registro_usuario_exitoso(client_db):
    response = client_db.post(
        "/usuarios/",
        json={"email": "nuevo@test.com", "password": "mipassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "nuevo@test.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_registro_usuario_email_duplicado(client_db):
    client_db.post(
        "/usuarios/",
        json={"email": "duplicado@test.com", "password": "pass"},
    )
    response = client_db.post(
        "/usuarios/",
        json={"email": "duplicado@test.com", "password": "otra"},
    )
    assert response.status_code == 400
    assert "ya está registrado" in response.json()["detail"]


def test_login_exitoso_y_fallido(client_db):
    client_db.post(
        "/usuarios/",
        json={"email": "login@test.com", "password": "mipassword123"},
    )

    # Login exitoso (form data OAuth2)
    res_login = client_db.post(
        "/usuarios/token",
        data={"username": "login@test.com", "password": "mipassword123"},
    )
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()
    assert res_login.json()["token_type"] == "bearer"

    # Login incorrecto
    res_err = client_db.post(
        "/usuarios/token",
        data={"username": "login@test.com", "password": "wrong"},
    )
    assert res_err.status_code == 401
