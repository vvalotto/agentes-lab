"""Módulo 2 — Aprobación de Cambio (8.2.1)."""

from __future__ import annotations

from github.GithubException import UnknownObjectException

from fastapi import APIRouter, Depends, Header, HTTPException

from .. import config
from ..agents.agente_aprobacion import redactar_aprobacion
from ..core import auth, state_machine
from ..core.github_tracker import GithubTracker
from ..core.models import AprobacionIn, AprobacionOut

router = APIRouter()

_tracker = GithubTracker(config.GITHUB_TOKEN, config.GITHUB_REPO)

_ACCION_POR_DECISION = {
    "aprobado": "aprobar",
    "aprobado_con_condiciones": "aprobar",
    "rechazado": "rechazar",
}


def _rol_autenticado(x_api_key: str = Header(..., description="API key del aprobador")) -> auth.Rol:
    try:
        return auth.resolver_rol(x_api_key, config.ROLES_API_KEYS)
    except auth.ApiKeyInvalidaError:
        raise HTTPException(status_code=401, detail="API key inválida o no reconocida")


@router.post("/solicitudes/{clave}/aprobacion", response_model=AprobacionOut)
def aprobar_solicitud(
    clave: str, datos: AprobacionIn, rol: auth.Rol = Depends(_rol_autenticado)
) -> AprobacionOut:
    try:
        issue = _tracker.obtener_issue(clave)
    except UnknownObjectException:
        raise HTTPException(status_code=404, detail=f"No existe el Issue {clave}")

    # Autorización por rol y clase — ANTES de tocar el agente o el Issue.
    try:
        auth.autorizar_aprobar(rol, datos.clase)
    except auth.NoAutorizadoError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # Transición válida — el estado actual del Issue tiene que admitir esta acción.
    accion = _ACCION_POR_DECISION[datos.decision]
    try:
        estado_nuevo = state_machine.transicionar(issue.estado, accion)
    except state_machine.TransicionInvalidaError as e:
        raise HTTPException(status_code=409, detail=str(e))

    comentario = redactar_aprobacion(datos)
    _tracker.comentar(clave, comentario)

    if accion == "aprobar":
        _tracker.set_clase_y_titulo(clave, datos.clase)
    _tracker.set_estado(clave, estado_nuevo)

    return AprobacionOut(clave=clave, estado_nuevo=estado_nuevo, decision=datos.decision)
