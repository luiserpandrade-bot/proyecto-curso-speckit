import os
from sqlalchemy import create_engine, inspect
from app.config import settings


def test_migracion_crea_tablas():
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    tablas = inspector.get_table_names()

    assert "usuarios" in tablas
    assert "gastos" in tablas

    columnas_usuarios = [c["name"] for c in inspector.get_columns("usuarios")]
    assert "id" in columnas_usuarios
    assert "email" in columnas_usuarios
    assert "hashed_password" in columnas_usuarios

    columnas_gastos = [c["name"] for c in inspector.get_columns("gastos")]
    assert "id" in columnas_gastos
    assert "descripcion" in columnas_gastos
    assert "monto" in columnas_gastos
    assert "categoria" in columnas_gastos
    assert "usuario_id" in columnas_gastos

    engine.dispose()
