# Tareas — Sistema de control de gastos

## Definition of done (aplica a TODAS las tareas de código)

Una tarea se considera terminada solo si cumple las tres condiciones:

1. Código escrito.
2. Test correspondiente escrito y **en verde**.
3. No viola ningún artículo de la constitución. Si hubo que desviarse, la
   desviación se declaró explícitamente y fue aprobada antes de continuar
   (sección Gobernanza).

Ninguna fase empieza antes de que la anterior esté completa y en verde, por
la dirección de dependencia del Artículo I.

---

## Fase 1 — Configuración y base de datos

**T1.1 — `pyproject.toml` y dependencias**
Declarar el proyecto como paquete instalable (`[build-system]` con hatchling,
`packages = ["app"]`) y agregar las dependencias del plan. Declarar
`[tool.coverage.run] omit` con `app/main.py`, `app/mcp/server.py`,
`app/mcp/auth.py` y `app/logging_config.py` (Artículo VII.3).
*Test:* `uv sync` y `python -c "import app"` desde otro directorio, apuntando
al intérprete del `.venv`.

**T1.2 — `app/config.py`**
`Settings(BaseSettings)` con `model_config = SettingsConfigDict(env_file=".env")`
y los campos: `secret_key` (obligatorio), `database_url`,
`access_token_expire_minutes`, `log_level`, `mcp_demo_email`,
`mcp_demo_password`, `mcp_issuer_url`, `mcp_resource_url`.
*Test:* `tests/test_config.py` — carga `Settings` y verifica que
`secret_key` es obligatorio y que los defaults son los declarados.
*Artículo:* IV.3.

**T1.3 — `.env` y `.env.example`**
`SECRET_KEY` generado con `secrets.token_hex(32)`, nunca escrito a mano.
`.env` en `.gitignore`; `.env.example` con las mismas claves y sin valores.
*Test:* verificación manual con `git check-ignore -q .env` (código de salida 0).
*Artículo:* IV.3.

**T1.4 — `app/database.py`**
`engine`, `SessionLocal`, `Base`, `get_db`. `connect_args` condicional: solo
se aplica `check_same_thread` si `database_url` empieza por `sqlite`.
*Test:* `tests/test_database.py` — verifica que `connect_args` queda vacío
con una URL de Postgres y poblado con una de SQLite.
*Artículo:* III.2.

**T1.5 — Modelos `Usuario` y `Gasto`**
`app/models/usuario.py` (id, email único indexado, hashed_password) y
`app/models/gasto.py` (id, descripcion, monto, categoria, usuario_id FK a
`usuarios.id`).
*Test:* `tests/test_modelos.py` — crea ambos contra SQLite en memoria y
verifica que la FK existe y que `email` es único.
*Artículo:* III.3, VIII (firma `Usuario(id=, email=, hashed_password=)`).

**T1.6 — Schemas Pydantic**
`app/schemas/usuario.py` (`UsuarioCreate`, `UsuarioResponse` sin
`hashed_password`) y `app/schemas/gasto.py` (`GastoCreate`, `GastoResponse`).
Usar `ConfigDict(from_attributes=True)`, no `class Config`.
*Test:* `tests/test_schemas.py` — verifica que `UsuarioResponse` no acepta
ni expone `hashed_password`, y que `GastoCreate` **no** declara `usuario_id`.
*Artículo:* IV.4, IV.6, V.3.

**T1.7 — Copiar los tests de referencia de las Sesiones 6-8**
Copiar `tests/__init__.py`, `tests/test_gastos.py`,
`tests/test_integracion_gastos.py` y `tests/test_api_gastos.py` desde el
proyecto de referencia en `C:\Users\Ups\proyecto-curso\tests\` al directorio
`tests/` del proyecto actual, **sin modificar sus aserciones**. Esta tarea
garantiza que los tests de compatibilidad existan en el repositorio desde la
Fase 1 y puedan actuar como compuerta de verificación (Definition of Done) en
las Fases 2, 4 y 6.
*Verificación:* los cuatro archivos existen en `tests/` del proyecto actual y
preservan sus aserciones intactas.
*Artículo:* VIII.1.

---

## Fase 2 — Repositories

**T2.1 — `app/repositories/usuarios.py`**
Módulo con funciones sueltas: `obtener_por_email(db, email) -> Usuario | None`
y `guardar(db, email, hashed_password) -> Usuario`. Sin reglas de negocio.
*Test:* cubierto por `tests/test_integracion_gastos.py` (copiado de S6-S8),
que usa `usuarios_repository.guardar` contra SQLite en memoria.
*Artículo:* I.3, VIII.2.

**T2.2 — `app/repositories/gastos.py`**
Funciones `guardar(db, usuario_id, descripcion, monto, categoria) -> dict`,
`listar(db, usuario_id, skip=0, limit=20) -> list[dict]`,
`total_por_categoria(db, usuario_id, categoria) -> float`. Devuelven `dict`,
nunca objetos ORM. **Toda** consulta filtra por `usuario_id`.
*Test:* `tests/test_repositorio_gastos.py` — inserta gastos de dos usuarios
distintos y verifica que `listar` y `total_por_categoria` de uno nunca
devuelven datos del otro.
*Artículo:* I.3, III.3, VIII.2.

---

## Fase 3 — Utils

**T3.1 — `app/utils/validadores.py`**
`CATEGORIAS_PERMITIDAS` como constante y `categoria_valida(categoria) -> bool`.
Función pura, sin imports de otras capas.
*Test:* `tests/test_validadores.py` — una categoría válida, una inválida, y
verificación de que agregar un valor a la constante no obliga a cambiar la
función (OCP).
*Artículo:* I.4, II.2.

**T3.2 — `app/utils/formato.py`**
`formatear_moneda(monto) -> str` con dos decimales.
*Test:* incluido en `tests/test_validadores.py` o archivo propio.
*Artículo:* I.4.

---

## Fase 4 — Services

**T4.1 — `app/services/gastos.py`**
`CategoriaInvalidaError`, `LimiteExcedidoError`, `LIMITE_POR_CATEGORIA = 500.0`,
`_validar_gasto(descripcion, monto, categoria)` separada de la orquestación,
`registrar_gasto(db, usuario_id, descripcion, monto, categoria, repo=gastos_repository) -> dict`
y `listar_gastos(db, usuario_id, skip=0, limit=20, repo=gastos_repository) -> list[dict]`.
Orden posicional exacto. **No importa SQLAlchemy.**
*Test:* `tests/test_gastos.py` (copiado de S6-S8, sin modificar aserciones) —
cubre los casos de error 1, 2 y 3 de `spec.md` con `RepositorioFalso`
inyectado por parámetro, sin `unittest.mock`.
*Artículo:* I.2, II.1, II.3, VII.2, VIII.1.

**T4.2 — `app/services/usuarios.py`**
`EmailYaRegistradoError`, `CredencialesInvalidasError`,
`registrar_usuario(db, email, password, repo=usuarios_repository)` y
`autenticar_usuario(db, email, password, repo=usuarios_repository)`.
*Test:* `tests/test_usuarios_service.py` — email duplicado lanza
`EmailYaRegistradoError`; contraseña incorrecta lanza
`CredencialesInvalidasError`; la contraseña nunca se devuelve ni se loguea.
*Artículo:* I.2, II.3, IV.1.

---

## Fase 5 — Seguridad y dependencies

**T5.1 — `app/security.py`**
`pwd_context` con bcrypt, `hash_password`, `verify_password`,
`crear_access_token` (HS256, expiración desde `settings`),
`decodificar_token`.
*Test:* `tests/test_security.py` — dos hashes de la misma contraseña son
distintos (salt); `verify_password` acepta la correcta y rechaza la
incorrecta; un token expirado o firmado con otra clave falla al decodificar.
*Artículo:* IV.1, IV.2.

**T5.2 — `app/dependencies.py`**
`oauth2_scheme`, `get_current_user` (decodifica el JWT, resuelve el usuario,
lanza `401` si falla) y `get_gastos_repo`.
*Test:* `tests/test_dependencies.py` — token inválido, token sin `sub`, y
token válido de un usuario inexistente devuelven `401`, no el usuario demo.
*Artículo:* IV.4, VII.5.

---

## Fase 6 — Routers

**T6.1 — `app/routers/usuarios.py`**
`POST /usuarios/` (201) y `POST /usuarios/token` (200). Traducen
`EmailYaRegistradoError` a `400` y `CredencialesInvalidasError` a `401`.
*Test:* `tests/test_api_usuarios.py` — registro exitoso devuelve `id` y
`email` pero nunca `hashed_password`; email duplicado devuelve `400`.
*Artículo:* I.1, V.1.

**T6.2 — `app/routers/gastos.py`**
`POST /gastos/` (201) y `GET /gastos/` (200) con `skip` y `limit`. Ambos
dependen de `get_current_user` y `get_gastos_repo`. **No declaran
`usuario_id` como parámetro en ninguna forma.**
Traducir explícitamente las excepciones de negocio provenientes de
`services/gastos.py` (`CategoriaInvalidaError` y `LimiteExcedidoError`) a
`HTTPException(status_code=400, detail=str(e))`.
*Test:* `tests/test_api_gastos.py` (copiado de S6-S8, sin modificar
aserciones) y `tests/test_api_gastos_errores.py` (nuevo test verificando que
`POST /gastos/` con categoría inválida responde HTTP 400 y que exceder el
límite de 500 responde HTTP 400, ambos con su mensaje en `detail`).
*Artículo:* I.1, IV.4, V.1, V.2, VII.3.

**T6.3 — `app/main.py`, logging y manejo de errores**
`configurar_logging`, middleware de logging de requests con duración, y
`@app.exception_handler(Exception)` devolviendo `500` con
`{"detail": "Error interno del servidor"}`.
*Test:* `tests/test_api_gastos.py` ya incluye
`test_error_no_controlado_devuelve_500_sin_stacktrace`.
*Artículo:* IV.5.

**T6.4 — Test del caso de error 4 de `spec.md` (401 sin token)** ⚠️ NUEVO
Los tests copiados de S6-S8 **no** cubren este caso, porque siempre
sobrescriben `get_current_user` con `dependency_overrides`.
*Test:* `tests/test_autorizacion.py` — `GET /gastos/` y `POST /gastos/`
**sin** header `Authorization` devuelven `401`, con `get_current_user`
**sin** sobrescribir.
*Artículo:* IV.4, VII.3 (cobertura de reglas).

**T6.5 — Test del caso de error 5 de `spec.md` (`usuario_id` ajeno ignorado)** ⚠️ NUEVO
Tampoco cubierto por los tests copiados.
*Test:* en `tests/test_autorizacion.py` — autenticado como el usuario A,
enviar `usuario_id` del usuario B en el body de `POST /gastos/` y como query
param en `GET /gastos/`. El gasto debe quedar bajo A, y el listado debe
devolver solo los de A. La respuesta **no** debe ser `403`: el parámetro se
ignora, no se rechaza (Artículo V.1).
*Artículo:* IV.4, V.1, VII.3.

---

## Fase 7 — Migraciones

**T7.1 — Alembic**
`alembic init alembic`, `env.py` apuntando a `settings.database_url` y a
`Base.metadata`, importando ambos modelos. Generar la migración inicial con
`--autogenerate` y aplicarla.
*Test:* la migración detecta las tablas `usuarios` y `gastos`; tras
`upgrade head`, ambas existen en la base.
*Artículo:* III.1.

---

## Fase 8 — MCP

**T8.1 — `app/mcp/auth.py`**
`JWTTokenVerifier` reutilizando `decodificar_token` de `app/security.py`.
Devuelve `None` si el token es inválido o no trae `sub`.
*Test:* `tests/test_mcp_auth.py` — token válido devuelve un `AccessToken`
con el `subject` correcto; token inválido devuelve `None`.
*Artículo:* IV.2, VI.4.

**T8.2 — `app/mcp/server.py`**
Instancia `FastMCP` con `streamable_http_path="/"`, `token_verifier` y
`AuthSettings` (con `validate_token_resource=False` y su comentario
explicando la simplificación). `tools/gastos.py` expone `register(mcp)`; es
`server.py` quien importa el módulo de tools, nunca al revés.
*Test:* `tests/test_mcp_server.py` — `mcp.list_tools()` devuelve exactamente
dos tools con descripciones no genéricas.
*Artículo:* VI.2.

**T8.3 — `app/mcp/tools/gastos.py`**
Tools `registrar_gasto` y `listar_gastos`, ambas llamando a
`services/gastos.py` sin reimplementar ninguna regla.
`_resolver_usuario_actual(db)` usa `get_access_token()`: si hay token, el
usuario sale de su `subject`; si el usuario del token no existe, se lanza
error, **nunca** se cae al demo. El usuario demo es el fallback solo cuando
no hay token, documentado con comentario.
*Test:* `tests/test_mcp_gastos.py` — un caso exitoso y un caso de error de
negocio (categoría inválida devuelve `{"error": ...}`); además, un test que
verifica que con token de un usuario inexistente **no** se opera como demo.
*Artículo:* VI.1, VI.2, VI.3, VI.4, VII.6.

**T8.4 — Montaje de MCP en `app/main.py`**
`streamable_http_app()` creado antes del lifespan; `session_manager.run()`
dentro del `lifespan`; `app.mount("/mcp", mcp_app)`. El fixture `client` de
`test_api_gastos.py` debe tener `scope="module"`.
*Test:* `tests/test_mcp_http.py` — `POST /mcp/` sin `Authorization` devuelve
`401` antes de ejecutar ninguna tool; REST sigue respondiendo igual en el
mismo proceso.
*Artículo:* VI.4, VII.5.

---

## Fase 9 — Verificación final

**T9.1 — Verificación final de tests de las Sesiones 6-8**
Ejecutar la suite copiada de referencia (`tests/test_gastos.py`,
`tests/test_integracion_gastos.py` y `tests/test_api_gastos.py`) con
`uv run pytest tests/test_gastos.py tests/test_integracion_gastos.py tests/test_api_gastos.py -v`.
*Verificación:* todos los tests de referencia pasan en verde sin haber
modificado sus aserciones originales.
*Artículo:* VIII.1.

**T9.2 — Verificación de cobertura** (tarea dedicada, no opcional)
Correr `uv run pytest --cov=app --cov-report=term-missing -v` y confirmar
explícitamente:
- Cobertura de `app/services/` ≥ 90%.
- Cobertura del conjunto `services/ + repositories/ + routers/ + utils/` ≥ 80%.
- Los 5 casos de error de `spec.md` tienen cada uno un test identificable.
Si el umbral no se cumple, indicar qué archivos o funciones quedaron sin
cubrir **antes** de dar el proyecto por terminado.
*Artículo:* VII.3.

---

## Mapa de casos de error → test

| # | Caso de `spec.md` | Test que lo cubre | Origen |
|---|---|---|---|
| 1 | Monto negativo o cero | `test_gastos.py::test_registrar_gasto_monto_invalido_lanza_error` | Copiado S6-S8 |
| 2 | Categoría inexistente | `test_gastos.py::test_registrar_gasto_categoria_invalida_lanza_error` | Copiado S6-S8 |
| 3 | Excede el límite de 500 | `test_gastos.py::test_registrar_gasto_excede_limite_categoria_lanza_error` | Copiado S6-S8 |
| 4 | Sin token → 401 | `test_autorizacion.py` (T6.4) | **Nuevo** |
| 5 | `usuario_id` ajeno ignorado | `test_autorizacion.py` (T6.5) | **Nuevo** |
| 6 | Errores de negocio en API → 400 (categoría inválida y límite excedido) | `tests/test_api_gastos_errores.py` (T6.2) | **Nuevo** |

