"""T8.1 — Verificación de Bearer tokens en MCP (Artículos IV.2 y VI.4)."""

import asyncio


from app.mcp.auth import JWTTokenVerifier
from app.security import crear_access_token


def test_token_valido_devuelve_access_token_con_subject():
    verifier = JWTTokenVerifier()
    token = crear_access_token({"sub": "usuario@ejemplo.com"})

    resultado = asyncio.run(verifier.verify_token(token))

    assert resultado is not None
    assert resultado.subject == "usuario@ejemplo.com"
    assert "gastos" in resultado.scopes


def test_token_invalido_devuelve_none():
    verifier = JWTTokenVerifier()

    assert asyncio.run(verifier.verify_token("token-falsificado")) is None


def test_token_sin_sub_devuelve_none():
    verifier = JWTTokenVerifier()
    token = crear_access_token({"otra_cosa": 123})

    assert asyncio.run(verifier.verify_token(token)) is None
