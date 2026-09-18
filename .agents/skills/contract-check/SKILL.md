---
name: contract-check
description: Verifica que las firmas del código coincidan con el "Contrato de compatibilidad" de spec.md, para que los tests copiados de las Sesiones 6-8 sigan importando y pasando.
---
# Instrucciones

1. Lee la sección "Contrato de compatibilidad" de `specs/*/spec.md`. Si no
   existe, DETENTE y avisa: sin contrato no hay nada que verificar.
2. Para cada símbolo listado en el contrato, comprueba en el código real:
   - que el módulo y el nombre existen,
   - que los parámetros coinciden en **nombre y orden posicional**,
   - que los que deben ser keyword con default (como `repo=`) lo son,
   - que el tipo de retorno es el declarado (`dict` y no un objeto ORM, por ejemplo).
3. Verifica además dos cosas estructurales que el contrato fija:
   - `repositories/gastos.py` y `repositories/usuarios.py` son módulos con
     funciones sueltas, **no clases**.
   - existe `tests/__init__.py`, porque `test_api_gastos.py` hace
     `from tests.test_gastos import RepositorioFalso`.
4. Reporta en esta tabla:

| Símbolo del contrato | Estado | Diferencia encontrada |
|---|---|---|

   Usa OK / DIFIERE / FALTA como estado.
5. Si hay alguna diferencia, corre `uv run pytest tests/test_gastos.py
   tests/test_integracion_gastos.py tests/test_api_gastos.py -v` y adjunta el
   resultado: un contrato roto se manifiesta como `ImportError` o `TypeError`
   en esos tres archivos.
6. **Nunca modifiques los tests copiados para que encajen con el código.** El
   contrato es el fijo; lo que se ajusta es el código.
