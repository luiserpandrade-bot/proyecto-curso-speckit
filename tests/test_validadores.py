from app.utils.validadores import categoria_valida, CATEGORIAS_PERMITIDAS


def test_categoria_valida():
    assert categoria_valida("comida") is True
    assert categoria_valida("transporte") is True
    assert categoria_valida("categoria_inexistente") is False
    assert categoria_valida("Comida") is False  # Validación estricta minúsculas


def test_ocp_categoria_valida(monkeypatch):
    # Demostrar que agregar una categoría a la constante la valida sin tocar la función
    monkeypatch.setattr(
        "app.utils.validadores.CATEGORIAS_PERMITIDAS",
        CATEGORIAS_PERMITIDAS | {"salud"},
    )
    assert categoria_valida("salud") is True
