from datetime import datetime, timedelta, timezone
import pytest
import jwt

from app.security import (
    hash_password,
    verify_password,
    crear_access_token,
    decodificar_token,
    ALGORITHM,
)


def test_hash_password_salt_diferente():
    p = "mi_contraseña_secreta"
    h1 = hash_password(p)
    h2 = hash_password(p)
    assert h1 != h2
    assert verify_password(p, h1) is True
    assert verify_password(p, h2) is True


def test_verify_password_rechaza_incorrecta():
    h = hash_password("clave_correcta")
    assert verify_password("clave_correcta", h) is True
    assert verify_password("clave_incorrecta", h) is False


def test_token_valido_y_decodificacion():
    token = crear_access_token({"sub": "usuario@test.com"})
    payload = decodificar_token(token)
    assert payload["sub"] == "usuario@test.com"
    assert "exp" in payload


def test_token_expirado_falla():
    exp_pasada = datetime.now(timezone.utc) - timedelta(minutes=5)
    token_expirado = jwt.encode(
        {"sub": "usuario@test.com", "exp": exp_pasada},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decodificar_token(token_expirado)


def test_token_firma_invalida_falla():
    token_otra_clave = jwt.encode(
        {"sub": "usuario@test.com"},
        "otra_clave_completamente_distinta_para_romper_la_firma_12345",
        algorithm=ALGORITHM,
    )
    with pytest.raises(jwt.InvalidSignatureError):
        decodificar_token(token_otra_clave)
