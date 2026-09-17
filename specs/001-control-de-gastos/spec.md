# Especificación — Sistema de control de gastos personales

## Clarifications

### Session 2026-09-16
- Q: ¿Cómo deben tratarse las mayúsculas y los espacios en blanco al validar y registrar la categoría de un gasto? → A: Validación estricta: coincidencia exacta en minúsculas sin espacios adicionales; cualquier variación lanza CategoriaInvalidaError.
- Q: ¿Cuál debe ser el criterio de ordenamiento de los gastos al consultarlos mediante el endpoint GET /gastos/ o la función listar_gastos? → A: Orden cronológico ascendente (por id ascendente / orden de creación).
- Q: ¿El límite de 500 por categoría se evalúa sobre el total histórico acumulado del usuario o se reinicia por mes calendario? → A: Acumulado histórico total (todos los gastos registrados del usuario en esa categoría sin discriminación por fechas, conforme a los tests de referencia).
- Q: ¿Qué validación de espacios y longitud máxima debe aplicarse al campo descripción de un gasto? → A: Inválida si queda vacía tras .strip(), con longitud máxima de 255 caracteres.
- Q: ¿Debe restringirse el monto de un gasto a un máximo de 2 cifras decimales o se permite cualquier valor flotante mayor a cero? → A: Flotante libre (cualquier valor flotante mayor a cero sin restricción forzada sobre el número de decimales).

## Entidades
- **Usuario**: email (único), contraseña (nunca expuesta en respuestas).
- **Gasto**: descripción, monto (> 0), categoría, pertenece a un usuario.

## Reglas de negocio
- Categorías válidas: `comida`, `transporte`, `entretenimiento`, `otros`.
  La coincidencia debe ser exacta en minúsculas y sin espacios; cualquier otra
  categoría o formato es un error de negocio (`CategoriaInvalidaError`), no una
  excepción genérica.
- El monto de un gasto debe ser un número flotante mayor a cero (sin límite
  obligatorio en la cantidad de cifras decimales); una descripción vacía o
  compuesta únicamente por espacios en blanco (tras aplicar `.strip()`) también
  es inválida. La longitud máxima de la descripción es de 255 caracteres.
- Un gasto no puede hacer que el total acumulado de su categoría supere 500.
  El cálculo se evalúa sobre el acumulado histórico total de los gastos del usuario
  en esa categoría (sin reinicio mensual ni filtro de fechas, consistente con la firma
  fijada de `total_por_categoria`).
- Un usuario solo puede ver y crear gastos propios; nunca los de otro usuario,
  sin importar qué identificador se pase en la solicitud.
- El listado de gastos (tanto en `GET /gastos/` como en `listar_gastos`) se
  ordena de forma determinista en orden cronológico ascendente (por `id` ascendente).

## Contrato de la API (REST)

| Método | Ruta              | Auth | Request                          | Éxito         | Errores esperados                          |
|--------|-------------------|------|-----------------------------------|---------------|---------------------------------------------|
| POST   | /usuarios/        | No   | email, password                   | 201 Usuario   | 400 email duplicado, 422 validación         |
| POST   | /usuarios/token   | No   | username, password (form)         | 200 token JWT | 401 credenciales inválidas                  |
| POST   | /gastos/          | Sí   | descripcion, monto, categoria     | 201 Gasto     | 400 categoría inválida, 400 límite excedido, 401, 422 |
| GET    | /gastos/          | Sí   | query: skip, limit                | 200 lista     | 401, 422 (skip/limit inválidos)             |

## Contrato equivalente por MCP
- Tool `registrar_gasto(descripcion, monto, categoria)`: mismo comportamiento
  y mismas reglas que `POST /gastos/`, devolviendo el gasto creado o un error
  de negocio estructurado.
- Tool `listar_gastos(skip=0, limit=20)`: mismo comportamiento que `GET /gastos/`.
- Ambas tools operan siempre sobre el usuario autenticado de la sesión MCP
  (identidad resuelta desde el token verificado cuando el transporte es
  streamable-http; usuario demo de `.env` solo como fallback documentado
  cuando el transporte es stdio sin identidad propagable), nunca sobre un
  usuario indicado como parámetro.

## Contrato de compatibilidad (no negociable)

Los tests de las Sesiones 6-8 se copian sin modificar. Fijan estas firmas —
sin esta sección, un agente que solo lea las reglas de negocio de arriba
tiene total libertad para inventar otras firmas, y los tres archivos de
tests fallan al importar:

- `app/services/gastos.py`: `CategoriaInvalidaError`, `LimiteExcedidoError`,
  `LIMITE_POR_CATEGORIA = 500.0`,
  `registrar_gasto(db, usuario_id, descripcion, monto, categoria, repo=gastos_repository) -> dict`,
  `listar_gastos(db, usuario_id, skip=0, limit=20, repo=gastos_repository) -> list[dict]`
  — orden posicional exacto, `repo` es keyword con default (DIP).
- `app/repositories/gastos.py` — módulo con funciones, NO clase:
  `guardar(db, usuario_id, descripcion, monto, categoria) -> dict`,
  `listar(db, usuario_id, skip=0, limit=20) -> list[dict]`,
  `total_por_categoria(db, usuario_id, categoria) -> float`. Devuelven
  `dict`, nunca objetos ORM.
- `app/repositories/usuarios.py`: `obtener_por_email(db, email) -> Usuario | None`,
  `guardar(db, email, hashed_password) -> Usuario`.
- `app.database.get_db`, `app.dependencies.get_current_user`,
  `app.dependencies.get_gastos_repo`, `app.models.usuario.Usuario(id=, email=,
  hashed_password=)` — los tests copiados los importan directamente.
- `tests/__init__.py` debe existir: `test_api_gastos.py` hace
  `from tests.test_gastos import RepositorioFalso`.

## Casos de error explícitos que deben tener test
1. Registrar gasto con monto negativo o cero.
2. Registrar gasto con categoría inexistente.
3. Registrar gasto que excede el límite de 500 en su categoría.
4. Listar o registrar gastos sin token → 401.
5. Listar gastos de otro usuario pasando su ID manualmente → debe ignorarse,
   nunca debe filtrar por ese ID.

> Los tests copiados de las Sesiones 6-8 cubren los casos 1 a 3. Los casos 4
> y 5 nunca se probaron en esas sesiones y requieren tests nuevos escritos en
> este proyecto.

## Ambigüedad resuelta (`/speckit-clarify`)

**Pregunta:** ¿puede un usuario con algún rol especial (por ejemplo,
administrador) ver o modificar gastos que no son suyos?

**Resolución:** No. Esta versión del sistema no define roles. El aislamiento
por usuario del Artículo IV.4 no admite excepciones: no existe ningún camino
—REST ni MCP— por el que un usuario acceda a gastos ajenos. Si en el futuro
se necesita un rol administrador, será una feature nueva con su propio ciclo
`/speckit-specify → /speckit-plan → /speckit-tasks → /speckit-implement`, no
una ampliación de esta spec.

## Alcance (qué NO entra en esta spec)

Esta spec cubre una sola funcionalidad: cómo un usuario controla sus gastos.
Quedan fuera, y merecerían su propio ciclo completo si se piden más adelante:
reportes mensuales exportables, notificaciones por correo, edición o
eliminación de gastos ya registrados, roles de administración y reinicio
periódico o mensual de límites acumulados por categoría.
