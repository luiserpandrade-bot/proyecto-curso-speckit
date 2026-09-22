# OCP: agregar una categoría nueva = agregar un valor aquí.
# La función de abajo nunca cambia.
CATEGORIAS_PERMITIDAS = {"transporte", "entretenimiento", "otros"}


def categoria_valida(categoria: str) -> bool:
    return categoria in CATEGORIAS_PERMITIDAS
