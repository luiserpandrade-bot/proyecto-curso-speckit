from app.schemas.usuario import UsuarioResponse
from app.schemas.gasto import GastoCreate
from app.models.usuario import Usuario


def test_usuario_response_no_expone_hashed_password():
    usuario_db = Usuario(id=1, email="test@ejemplo.com", hashed_password="super-secret-hash")
    response = UsuarioResponse.model_validate(usuario_db)

    data = response.model_dump()
    assert "hashed_password" not in data
    assert "password" not in data
    assert data["id"] == 1
    assert data["email"] == "test@ejemplo.com"


def test_gasto_create_no_declara_usuario_id():
    # GastoCreate no debe tener usuario_id en sus campos
    assert "usuario_id" not in GastoCreate.model_fields

    # Si se pasa usuario_id en el payload de entrada, no se asigna al modelo validado
    gasto = GastoCreate(descripcion="Cena", monto=40.0, categoria="comida", usuario_id=99)
    data = gasto.model_dump()
    assert "usuario_id" not in data
    assert data == {"descripcion": "Cena", "monto": 40.0, "categoria": "comida"}
