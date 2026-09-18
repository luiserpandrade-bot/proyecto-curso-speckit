---
name: constitution-check
description: Revisa un archivo o un cambio propuesto contra los 8 artículos de .specify/memory/constitution.md y reporta cada violación con el número de artículo que incumple.
---
# Instrucciones

1. Lee `.specify/memory/constitution.md` completa. Si no existe, DETENTE y avisa:
   sin constitución no hay nada contra qué verificar, y no debes inventar criterios propios.
2. Lee el archivo o el diff que se te indique. Si no se indica ninguno, revisa
   los archivos con cambios sin commitear (`git diff --name-only`).
3. Para cada uno de los 8 artículos, evalúa si el código lo cumple, lo incumple
   o no le aplica. Presta atención especial a estos tres, que son los que más
   se violan por descuido:
   - **II.3 (DIP)**: toda función de `services/` que use un repository debe
     recibirlo como parámetro con default (`repo=...`), nunca importarlo fijo
     dentro del cuerpo.
   - **IV.1 (hashing)**: solo `passlib[bcrypt]`. Cualquier fallback a otra
     librería de hashing (hashlib, sha256, md5) es una violación, incluso
     dentro de un `try/except ImportError`.
   - **IV.4 (autorización)**: el `usuario_id` sale del token, nunca de la URL,
     el body o un query param.
4. Reporta en esta tabla, una fila por hallazgo:

| Archivo:línea | Artículo | Qué incumple | Corrección sugerida |
|---|---|---|---|

5. Si no hay hallazgos, dilo explícitamente en una línea: no inventes
   observaciones menores para llenar la tabla.
6. **No corrijas el código.** Esta skill diagnostica; la corrección la decide
   quien la invocó, porque la sección Gobernanza exige aprobación explícita
   antes de desviarse de un artículo.
