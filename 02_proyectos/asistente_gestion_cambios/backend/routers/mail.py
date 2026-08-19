"""Canal mail para el Módulo 1 — solo lectura del buzón (IMAP). No crea
Issues ni toca SolicitudIn: lista y lee correos crudos; el contenido se
manda tal cual a POST /chat/mensaje desde el frontend, reusando el canal
chat completo sin duplicar lógica de negocio."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from .. import config
from ..core import auth, mail_reader
from ..core.models import CorreoContenido, CorreoResumen
from ._common import rol_autenticado

router = APIRouter()


def _requerir_imap_configurado():
    if not config.IMAP_USER or not config.IMAP_APP_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="Canal mail no configurado — falta IMAP_USER/IMAP_APP_PASSWORD en el .env.",
        )


@router.get("/mail/recientes", response_model=list[CorreoResumen])
def listar_recientes(rol: auth.Rol = Depends(rol_autenticado)) -> list[CorreoResumen]:
    try:
        auth.autorizar_crear(rol)
    except auth.NoAutorizadoError as e:
        raise HTTPException(status_code=403, detail=str(e))

    _requerir_imap_configurado()
    return mail_reader.listar_recientes()


@router.get("/mail/{uid}", response_model=CorreoContenido)
def leer_correo(uid: str, rol: auth.Rol = Depends(rol_autenticado)) -> CorreoContenido:
    try:
        auth.autorizar_crear(rol)
    except auth.NoAutorizadoError as e:
        raise HTTPException(status_code=403, detail=str(e))

    _requerir_imap_configurado()
    try:
        contenido = mail_reader.leer_correo(uid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return CorreoContenido(contenido=contenido)
