import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.logging_config import configurar_logging
from app.routers import usuarios, gastos
from app.mcp.server import mcp as mcp_server

configurar_logging(settings.log_level)
logger = logging.getLogger(__name__)

# Streamable-HTTP: el mismo servidor MCP de hoy (mismos tools, mismo
# services/gastos.py), servido como una sub-app ASGI montable en FastAPI.
# Se crea ANTES de entrar al lifespan: mcp_server.session_manager es lazy y
# solo existe después de llamar a streamable_http_app().
mcp_app = mcp_server.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # mcp_app trae su propio lifespan (arranca el session manager de streamable-http).
    # FastAPI NO lo arranca solo por estar montado con app.mount() -- hay que entrar a él
    # explícitamente, o las conexiones a /mcp fallan o cuelgan.
    async with mcp_server.session_manager.run():
        yield


app = FastAPI(title="API de Control de Gastos", lifespan=lifespan)
app.include_router(usuarios.router)
app.include_router(gastos.router)
app.mount("/mcp", mcp_app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    inicio = time.perf_counter()
    response = await call_next(request)
    duracion_ms = (time.perf_counter() - inicio) * 1000
    logger.info(
        "%s %s -> %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duracion_ms,
    )
    return response


@app.exception_handler(Exception)
async def manejar_error_no_controlado(request: Request, exc: Exception):
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})
