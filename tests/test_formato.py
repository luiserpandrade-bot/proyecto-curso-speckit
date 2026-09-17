from app.utils.formato import formatear_moneda


def test_formatear_moneda():
    assert formatear_moneda(12.5) == "$12.50"
    assert formatear_moneda(1000.0) == "$1,000.00"
    assert formatear_moneda(0.0) == "$0.00"
