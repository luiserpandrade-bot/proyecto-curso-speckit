#!/bin/bash
# Bloquea el commit si la suite no pasa.
# Se invoca el Python del .venv directamente: el bash de Git para Windows
# no tiene 'uv' en su PATH.
cd ..
if [ -x ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"
else
  PY=".venv/bin/python"
fi
if "$PY" -m pytest --tb=no -q > .pre-commit.log 2>&1; then
  echo '{}'
else
  echo '{"decision":"block","reason":"Hay tests fallando. Corrige el codigo antes de hacer commit."}'
fi