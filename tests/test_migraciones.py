"""T7.1 — Las migraciones de Alembic crean las tablas esperadas.

El test aplica las migraciones sobre una base temporal propia, en vez de
inspeccionar el gastos.db del entorno de desarrollo: así es autocontenido y
pasa igual en una máquina limpia o en el runner de CI, donde ese archivo
no existe.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect


@pytest.fixture
def db_migrada(tmp_path, monkeypatch):
    destino = tmp_path / "test_migraciones.db"
    url = f"sqlite:///{destino}"
    monkeypatch.setenv("DATABASE_URL", url)

    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, resultado.stderr

    engine = create_engine(url)
    yield engine
    engine.dispose()


def test_migracion_crea_tablas(db_migrada):
    inspector = inspect(db_migrada)
    tablas = inspector.get_table_names()

    assert "usuarios" in tablas
    assert "gastos" in tablas

    columnas_usuarios = [c["name"] for c in inspector.get_columns("usuarios")]
    assert "id" in columnas_usuarios
    assert "email" in columnas_usuarios
    assert "hashed_password" in columnas_usuarios

    columnas_gastos = [c["name"] for c in inspector.get_columns("gastos")]
    for col in ("id", "descripcion", "monto", "categoria", "usuario_id"):
        assert col in columnas_gastos
