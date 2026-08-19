"""Módulo 1 — Solicitud de Cambio (8.2.1). Canal: formulario HTTP directo."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from .. import config
from ..agents.agente_solicitud import redactar_solicitud
from ..core import auth, casos_de_uso
from ..core.github_tracker import GithubTracker
from ..core.models import SolicitudIn, SolicitudOut
from ._common import rol_autenticado

router = APIRouter()

_tracker = GithubTracker(config.GITHUB_TOKEN, config.GITHUB_REPO)


@router.post("/solicitudes", response_model=SolicitudOut, status_code=201)
def crear_solicitud(datos: SolicitudIn, rol: auth.Rol = Depends(rol_autenticado)) -> SolicitudOut:
    try:
        return casos_de_uso.crear_solicitud(datos, rol, _tracker, redactar_solicitud)
    except auth.NoAutorizadoError as e:
        raise HTTPException(status_code=403, detail=str(e))
