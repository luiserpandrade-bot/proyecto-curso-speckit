from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.repositories import usuarios as usuarios_repo


def test_guardar_y_obtener_usuario():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    usuario = usuarios_repo.guardar(db, "test@correo.com", "hash123")
    assert usuario.id is not None
    assert usuario.email == "test@correo.com"
    assert usuario.hashed_password == "hash123"

    recuperado = usuarios_repo.obtener_por_email(db, "test@correo.com")
    assert recuperado is not None
    assert recuperado.id == usuario.id

    no_existe = usuarios_repo.obtener_por_email(db, "inexistente@correo.com")
    assert no_existe is None

    db.close()
    Base.metadata.drop_all(engine)
