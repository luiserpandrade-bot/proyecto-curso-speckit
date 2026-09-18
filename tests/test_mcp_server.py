"""T8.2 — El servidor MCP registra exactamente dos tools (Artículo VI.2)."""

import asyncio

from app.mcp.server import mcp


def test_registra_exactamente_dos_tools():
    tools = asyncio.run(mcp.list_tools())
    nombres = {t.name for t in tools}

    assert nombres == {"registrar_gasto", "listar_gastos"}


def test_descripciones_no_son_genericas():
    """Artículo VI.2: la descripción debe ser específica y accionable."""
    tools = asyncio.run(mcp.list_tools())

    for tool in tools:
        assert tool.description, f"{tool.name} no tiene descripción"
        assert len(tool.description) > 40, f"{tool.name} tiene una descripción demasiado escueta"
        assert tool.description.lower() != "maneja gastos"
