"""Carga de configuración desde el entorno (.env de este proyecto).

No hay valores por defecto para secretos: si falta algo, falla al arrancar
en vez de arrancar en un estado a medias.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _requerida(nombre: str) -> str:
    valor = os.environ.get(nombre)
    if not valor:
        raise RuntimeError(
            f"Falta la variable de entorno '{nombre}'. Revisá {_ENV_PATH} "
            f"(copiá .env.example si no existe todavía)."
        )
    return valor


def _parsear_roles_api_keys(crudo: str) -> dict[str, str]:
    """Formato: 'key1:rol1,key2:rol2,...' -> {'key1': 'rol1', 'key2': 'rol2'}"""
    resultado: dict[str, str] = {}
    for par in crudo.split(","):
        par = par.strip()
        if not par:
            continue
        clave, _, rol = par.partition(":")
        if not clave or not rol:
            raise RuntimeError(
                f"Entrada inválida en ROLES_API_KEYS: '{par}' (esperado 'api_key:rol')"
            )
        resultado[clave] = rol
    return resultado


GITHUB_TOKEN = _requerida("GITHUB_TOKEN")
GITHUB_REPO = _requerida("GITHUB_REPO")  # formato "owner/repo"
ANTHROPIC_API_KEY = _requerida("ANTHROPIC_API_KEY")
ROLES_API_KEYS = _parsear_roles_api_keys(_requerida("ROLES_API_KEYS"))
