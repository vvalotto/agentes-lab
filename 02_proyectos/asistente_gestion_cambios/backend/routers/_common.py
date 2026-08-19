"""Dependencies de FastAPI compartidas entre routers.

Separado de core/auth.py a propósito: ese módulo es lógica de negocio pura
(sin FastAPI), testeable sola. Esto es el pegamento HTTP alrededor."""

from __future__ import annotations

from fastapi import Header, HTTPException

from .. import config
from ..core import auth


def rol_autenticado(x_api_key: str = Header(..., description="API key de quien llama")) -> auth.Rol:
    try:
        return auth.resolver_rol(x_api_key, config.ROLES_API_KEYS)
    except auth.ApiKeyInvalidaError:
        raise HTTPException(status_code=401, detail="API key inválida o no reconocida")
