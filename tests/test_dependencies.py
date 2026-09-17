import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.dependencies import get_current_user, get_gastos_repo
from app.security import crear_access_token
from app.repositories import gastos as gastos_repo


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()
    Base.metadata.drop_all(engine)


def test_get_gastos_repo():
    assert get_gastos_repo() is gastos_repo


def test_get_current_user_token_invalido(db_session):
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="token_invalido_totalmente", db=db_session)
    assert exc.value.status_code == 401


def test_get_current_user_token_sin_sub(db_session):
    token_sin_sub = crear_access_token({"otra_cosa": 123})
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token_sin_sub, db=db_session)
    assert exc.value.status_code == 401


def test_get_current_user_usuario_inexistente(db_session):
    token_valido_usuario_inexistente = crear_access_token({"sub": "fantasma@ejemplo.com"})
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token_valido_usuario_inexistente, db=db_session)
    assert exc.value.status_code == 401
