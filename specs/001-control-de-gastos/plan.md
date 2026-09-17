# Plan técnico — Sistema de control de gastos

## Stack

FastAPI, `uvicorn[standard]`, SQLAlchemy + Alembic, `pyjwt`,
`passlib[bcrypt]`, `bcrypt<4.1`, `pydantic-settings`, `email-validator`,
`python-multipart`, SDK oficial `mcp` (`mcp[cli]<2`) montado vía
streamable-http, `pytest` + `pytest-cov` + `httpx`.

## Estructura de paquetes

```
app/
├── main.py             # arranque: FastAPI + lifespan + mount de MCP
├── config.py           # Settings (pydantic-settings) leyendo .env
├── database.py         # engine, SessionLocal, Base, get_db
├── dependencies.py     # get_current_user, get_gastos_repo
├── security.py         # hashing, creación y decodificación de JWT
├── logging_config.py
├── models/             # tablas SQLAlchemy
├── schemas/            # Pydantic de entrada/salida
├── repositories/       # única capa que toca la base de datos
├── services/           # lógica de negocio
├── routers/            # endpoints REST
├── utils/              # funciones puras
└── mcp/
    ├── server.py
    ├── auth.py
    └── tools/gastos.py
```

## Trazabilidad plan → constitución

- **Artículo I (capas).** La separación `routers/` / `services/` /
  `repositories/` / `utils/` se implementa como paquetes Python separados
  bajo `app/`, sin imports cruzados que violen la dirección de dependencia.
  Un `service` importa su `repository`; nunca al revés. `utils/` no importa
  nada de las otras tres.

- **Artículo II.3 (DIP).** Se implementa con parámetros por defecto en las
  funciones de `services/` (`def registrar_gasto(..., repo=gastos_repository)`),
  no con un contenedor de inyección de dependencias externo — mantenerlo
  simple. Es lo que permite cumplir el Artículo VII.2 sin `unittest.mock`.

- **Artículo II.2 (OCP).** Las categorías válidas viven en una constante
  `CATEGORIAS_PERMITIDAS` en `app/utils/validadores.py`. Agregar una
  categoría es agregar un valor al conjunto; la función `categoria_valida`
  no cambia.

- **Artículo III (persistencia).** SQLAlchemy con modelos declarativos y
  Alembic para migraciones. `database.py` aplica `connect_args={"check_same_thread": False}`
  solo cuando la URL empieza por `sqlite`, de modo que cambiar
  `DATABASE_URL` a Postgres no obliga a tocar `services/` ni `routers/`.
  El modelo `Gasto` declara `usuario_id` como FK a `usuarios.id`, y toda
  consulta de `repositories/gastos.py` filtra por él.

- **Artículo IV (seguridad).** `pyjwt` para JWT — una sola librería, no
  "pyjwt o python-jose": dar a elegir reintroduce la ambigüedad que la
  constitución existe para eliminar, y python-jose está sin mantenimiento.
  `passlib.context.CryptContext(schemes=["bcrypt"])` para hashing, con
  `bcrypt<4.1` fijado porque passlib 1.7.4 rompe en runtime con versiones
  más nuevas. `pydantic_settings.BaseSettings` leyendo `.env` para
  `SECRET_KEY` y `DATABASE_URL`. `email-validator` y `python-multipart` son
  dependencias transitivas obligatorias de `pydantic.EmailStr` y
  `OAuth2PasswordRequestForm` respectivamente — sin ellas la app ni siquiera
  arranca.

- **Artículo IV.4 (autorización).** Toda ruta y tool que opera sobre gastos
  depende de `get_current_user` (o su equivalente MCP) para obtener el
  `usuario_id`. Ningún endpoint acepta `usuario_id` como parámetro de
  entrada: no aparece en la ruta, ni en el body, ni como query param. El
  schema `GastoCreate` no lo declara, de modo que Pydantic lo descartaría
  aunque el cliente lo enviara.

- **Artículo IV.5 (errores no controlados).** Un `@app.exception_handler(Exception)`
  en `main.py` devuelve `500` con `{"detail": "Error interno del servidor"}`
  y registra el detalle con `logger.exception`, nunca lo expone al cliente.

- **Artículo V (endpoints).** Los códigos de estado se fijan en el decorador
  (`status_code=201` en los POST) y las excepciones de negocio de
  `services/` se traducen a `400` en el router con `HTTPException`. `skip` y
  `limit` son query params con defaults `0` y `20`; valores inválidos los
  rechaza Pydantic con `422` sin llegar al service.

- **Artículo VI (MCP).** El servidor se monta dentro de la misma app FastAPI
  con `streamable_http_app()` y `app.mount("/mcp", ...)`, entrando
  explícitamente al `session_manager.run()` desde el `lifespan`. La
  identidad se resuelve con `get_access_token()`: si hay token verificado se
  usa su `subject`; el usuario demo de `.env` es el único fallback y solo
  cuando no hay token (stdio), documentado con un comentario. Las tools
  llaman a `services/gastos.py`; no reimplementan ninguna regla.

- **Artículo VII (testing).** Fixtures de pytest con SQLite en memoria para
  los tests de integración, `app.dependency_overrides` para los de API
  (`httpx` como dependencia de `TestClient`), y `pytest-cov` con el umbral
  del Artículo VII.3 verificado como última tarea de `/speckit-implement`,
  no como tarea opcional. Las exclusiones de cobertura (`main.py`,
  `mcp/server.py`, `mcp/auth.py`, `logging_config.py`) se declaran en
  `[tool.coverage.run] omit` de `pyproject.toml`.

- **Artículo VIII (compatibilidad).** Las firmas del "Contrato de
  compatibilidad" de `spec.md` se implementan literalmente: mismo nombre,
  mismo orden posicional, `repo` como keyword con default. Los repositories
  son módulos con funciones sueltas, no clases, y devuelven `dict`. El
  proyecto se declara como paquete instalable en `pyproject.toml`
  (`[build-system]` con hatchling y `packages = ["app"]`) para que `app` sea
  importable desde cualquier punto de entrada, incluido el CLI de `mcp`.

## Orden de construcción

La dirección de dependencia del Artículo I fija el orden y ninguna fase
empieza antes de que la anterior esté en verde:

1. Configuración, base de datos y modelos
2. Repositories
3. Utils (funciones puras, sin dependencias)
4. Services
5. Seguridad (hashing, JWT) y dependencies
6. Routers
7. Migraciones de Alembic
8. MCP (server, auth, tools)
9. Verificación de cobertura
