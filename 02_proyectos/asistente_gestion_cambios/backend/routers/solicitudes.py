"""Módulo 1 — Solicitud de Cambio (8.2.1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from .. import config
from ..agents.agente_solicitud import redactar_solicitud
from ..core import auth
from ..core.github_tracker import GithubTracker, armar_titulo
from ..core.models import SolicitudIn, SolicitudOut

router = APIRouter()

_tracker = GithubTracker(config.GITHUB_TOKEN, config.GITHUB_REPO)


def _rol_autenticado(x_api_key: str = Header(..., description="API key del solicitante")) -> auth.Rol:
    try:
        return auth.resolver_rol(x_api_key, config.ROLES_API_KEYS)
    except auth.ApiKeyInvalidaError:
        raise HTTPException(status_code=401, detail="API key inválida o no reconocida")


@router.post("/solicitudes", response_model=SolicitudOut, status_code=201)
def crear_solicitud(datos: SolicitudIn, rol: auth.Rol = Depends(_rol_autenticado)) -> SolicitudOut:
    try:
        auth.autorizar_crear(rol)
    except auth.NoAutorizadoError as e:
        raise HTTPException(status_code=403, detail=str(e))

    descripcion = redactar_solicitud(datos)
    titulo_issue = armar_titulo(datos.titulo, datos.elemento_configuracion)
    issue = _tracker.crear_issue(titulo_issue, descripcion)

    return SolicitudOut(clave=issue.clave, url=issue.url, estado=issue.estado)
