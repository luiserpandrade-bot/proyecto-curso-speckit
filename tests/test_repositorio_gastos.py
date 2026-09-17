from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.repositories import usuarios as usuarios_repo
from app.repositories import gastos as gastos_repo


def test_repositorio_gastos_aislamiento_por_usuario():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    u1 = usuarios_repo.guardar(db, "u1@ejemplo.com", "pass1")
    u2 = usuarios_repo.guardar(db, "u2@ejemplo.com", "pass2")

    # Guardar gastos para ambos usuarios
    g1 = gastos_repo.guardar(db, u1.id, "Almuerzo U1", 30.0, "comida")
    g2 = gastos_repo.guardar(db, u1.id, "Metro U1", 10.0, "transporte")
    g3 = gastos_repo.guardar(db, u2.id, "Cena U2", 80.0, "comida")

    # Verificar retorno tipo dict
    assert isinstance(g1, dict)
    assert g1["descripcion"] == "Almuerzo U1"

    # Verificar que u1 solo lista sus gastos
    lista_u1 = gastos_repo.listar(db, u1.id)
    assert len(lista_u1) == 2
    assert [g["descripcion"] for g in lista_u1] == ["Almuerzo U1", "Metro U1"]

    # Verificar que u2 solo lista sus gastos
    lista_u2 = gastos_repo.listar(db, u2.id)
    assert len(lista_u2) == 1
    assert lista_u2[0]["descripcion"] == "Cena U2"

    # Verificar total_por_categoria aislado
    assert gastos_repo.total_por_categoria(db, u1.id, "comida") == 30.0
    assert gastos_repo.total_por_categoria(db, u2.id, "comida") == 80.0
    assert gastos_repo.total_por_categoria(db, u1.id, "transporte") == 10.0
    assert gastos_repo.total_por_categoria(db, u2.id, "transporte") == 0.0

    db.close()
    Base.metadata.drop_all(engine)
