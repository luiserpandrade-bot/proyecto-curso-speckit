import pytest
from app.services.usuarios import (
    registrar_usuario,
    autenticar_usuario,
    EmailYaRegistradoError,
    CredencialesInvalidasError,
)
from app.models.usuario import Usuario


class RepositorioUsuariosFalso:
    def __init__(self):
        self._usuarios: list[Usuario] = []

    def obtener_por_email(self, db, email: str):
        for u in self._usuarios:
            if u.email == email:
                return u
        return None

    def guardar(self, db, email: str, hashed_password: str):
        usuario = Usuario(
            id=len(self._usuarios) + 1,
            email=email,
            hashed_password=hashed_password,
        )
        self._usuarios.append(usuario)
        return usuario


def test_registrar_usuario_exitoso():
    repo = RepositorioUsuariosFalso()
    usuario = registrar_usuario(None, "nuevo@ejemplo.com", "password123", repo=repo)
    assert usuario.email == "nuevo@ejemplo.com"
    # Contraseña nunca en texto plano
    assert usuario.hashed_password != "password123"
    assert usuario.hashed_password.startswith("$2b$") or usuario.hashed_password.startswith("$2a$")


def test_registrar_usuario_email_duplicado():
    repo = RepositorioUsuariosFalso()
    registrar_usuario(None, "duplicado@ejemplo.com", "password123", repo=repo)
    with pytest.raises(EmailYaRegistradoError):
        registrar_usuario(None, "duplicado@ejemplo.com", "otro_password", repo=repo)


def test_autenticar_usuario_exitoso_e_invalido():
    repo = RepositorioUsuariosFalso()
    registrar_usuario(None, "auth@ejemplo.com", "clave_correcta", repo=repo)

    # Autenticación correcta
    usuario = autenticar_usuario(None, "auth@ejemplo.com", "clave_correcta", repo=repo)
    assert usuario.email == "auth@ejemplo.com"

    # Contraseña incorrecta
    with pytest.raises(CredencialesInvalidasError):
        autenticar_usuario(None, "auth@ejemplo.com", "clave_erronea", repo=repo)

    # Usuario inexistente
    with pytest.raises(CredencialesInvalidasError):
        autenticar_usuario(None, "noexiste@ejemplo.com", "clave_correcta", repo=repo)
