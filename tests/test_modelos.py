import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.models.usuario import Usuario
from app.models.gasto import Gasto


def test_modelos_usuario_y_gasto_sqlite():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Verificar creación de usuario y compatibilidad de firma Usuario(id=, email=, hashed_password=)
    usuario = Usuario(id=1, email="test@ejemplo.com", hashed_password="hashed_secret")
    db.add(usuario)
    db.commit()

    # Verificar unicidad de email
    usuario_duplicado = Usuario(email="test@ejemplo.com", hashed_password="otro_password")
    db.add(usuario_duplicado)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Verificar creación de gasto con FK a usuario
    gasto = Gasto(
        id=1,
        descripcion="Almuerzo",
        monto=25.5,
        categoria="comida",
        usuario_id=usuario.id,
    )
    db.add(gasto)
    db.commit()

    gasto_db = db.query(Gasto).filter_by(id=1).first()
    assert gasto_db is not None
    assert gasto_db.usuario_id == usuario.id
    assert gasto_db.monto == 25.5
    assert gasto_db.categoria == "comida"

    # Verificar que Gasto tiene FK hacia usuarios.id
    fks = [fk.target_fullname for fk in Gasto.__table__.foreign_keys]
    assert "usuarios.id" in fks

    db.close()
    Base.metadata.drop_all(engine)
