"""Canal chat para el Módulo 1 (8.2.1) — mismo destino que el formulario
(POST /solicitudes), entrada distinta: lenguaje libre en vez de campos
estructurados. Ver backend/agents/agente_extraccion.py para el porqué de
las dos llamadas acotadas por turno en vez de un loop abierto."""

from __future__ import annotations

import pydantic
from fastapi import APIRouter, Depends, HTTPException

from .. import config
from ..agents.agente_extraccion import extraer_campos, preguntar_por_faltantes
from ..agents.agente_solicitud import redactar_solicitud
from ..core import auth, casos_de_uso, conversaciones
from ..core.github_tracker import GithubTracker
from ..core.models import MensajeChatIn, MensajeChatOut, SolicitudIn
from ._common import rol_autenticado

router = APIRouter()

_tracker = GithubTracker(config.GITHUB_TOKEN, config.GITHUB_REPO)


@router.post("/chat/mensaje", response_model=MensajeChatOut)
def enviar_mensaje(datos: MensajeChatIn, rol: auth.Rol = Depends(rol_autenticado)) -> MensajeChatOut:
    try:
        auth.autorizar_crear(rol)
    except auth.NoAutorizadoError as e:
        raise HTTPException(status_code=403, detail=str(e))

    conversacion_id = datos.conversacion_id or conversaciones.nueva_conversacion()
    historial = conversaciones.agregar_mensaje(conversacion_id, datos.mensaje)

    campos = extraer_campos(historial)
    campos_no_vacios = {clave: valor for clave, valor in campos.items() if valor}

    try:
        solicitud_datos = SolicitudIn(**campos_no_vacios)
    except pydantic.ValidationError as e:
        campos_faltantes = [str(err["loc"][0]) for err in e.errors()]
        pregunta = preguntar_por_faltantes(campos, campos_faltantes)
        return MensajeChatOut(conversacion_id=conversacion_id, respuesta=pregunta, solicitud=None)

    solicitud = casos_de_uso.crear_solicitud(solicitud_datos, rol, _tracker, redactar_solicitud)
    conversaciones.cerrar_conversacion(conversacion_id)

    respuesta = (
        f"Listo — registré la solicitud como {solicitud.clave}, "
        f"en estado {solicitud.estado}. La vas a poder ver en {solicitud.url}."
    )
    return MensajeChatOut(conversacion_id=conversacion_id, respuesta=respuesta, solicitud=solicitud)
