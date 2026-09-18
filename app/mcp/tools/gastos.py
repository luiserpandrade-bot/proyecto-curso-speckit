from mcp.server.fastmcp import FastMCP
from mcp.server.auth.middleware.auth_context import get_access_token
from app.config import settings
from app.database import SessionLocal
from app.repositories import usuarios as usuarios_repository
from app.services import gastos as gastos_service
from app.security import hash_password


def _obtener_o_crear_usuario_demo(db):
    """
    Simplificación intencional de esta práctica, ahora acotada a stdio: ese
    transporte no tiene forma de portar un Bearer token, así que sigue usando
    un usuario de demostración fijo. Sobre HTTP (streamable-http/sse), el
    Bearer token (mismo JWT de la Sesión 7) sí identifica al usuario real --
    ver JWTTokenVerifier (app/mcp/auth.py) y _resolver_usuario_actual abajo.

    El email/password del usuario demo vienen de Settings (.env), no quemados
    en el código -- mismo patrón que SECRET_KEY/DATABASE_URL desde la S7.
    """
    usuario = usuarios_repository.obtener_por_email(db, settings.mcp_demo_email)
    if usuario is None:
        usuario = usuarios_repository.guardar(
            db, settings.mcp_demo_email, hash_password(settings.mcp_demo_password)
        )
    return usuario


def _resolver_usuario_actual(db):
    access_token = get_access_token()
    if access_token is None:
        # Sin token solo puede ser stdio: sobre HTTP, RequireAuthMiddleware ya
        # respondió 401 antes de llegar aquí.
        return _obtener_o_crear_usuario_demo(db)

    usuario = None
    if access_token.subject:
        usuario = usuarios_repository.obtener_por_email(db, access_token.subject)
    if usuario is None:
        # Hay token pero no corresponde a nadie (p. ej. usuario borrado):
        # se rechaza. NUNCA se cae al usuario demo cuando hay un token de por medio.
        raise ValueError("El token no corresponde a ningún usuario registrado")
    return usuario


def register(mcp: FastMCP) -> None:
    """Registra los tools de gastos sobre la instancia de FastMCP que le pasa server.py."""

    @mcp.tool()
    def registrar_gasto(descripcion: str, monto: float, categoria: str) -> dict:
        """Registra un nuevo gasto. Usar cuando el usuario mencione una compra o pago que quiere trackear."""
        db = SessionLocal()
        try:
            usuario = _resolver_usuario_actual(db)
            return gastos_service.registrar_gasto(db, usuario.id, descripcion, monto, categoria)
        except (ValueError, gastos_service.CategoriaInvalidaError, gastos_service.LimiteExcedidoError) as e:
            # Manejo de errores en tools: se devuelve texto claro, no una excepción sin control
            return {"error": str(e)}
        finally:
            db.close()

    @mcp.tool()
    def listar_gastos() -> list[dict]:
        """Lista todos los gastos registrados del usuario. Usar cuando pregunten por sus gastos o quieran un resumen."""
        db = SessionLocal()
        try:
            usuario = _resolver_usuario_actual(db)
            return gastos_service.listar_gastos(db, usuario.id)
        finally:
            db.close()
