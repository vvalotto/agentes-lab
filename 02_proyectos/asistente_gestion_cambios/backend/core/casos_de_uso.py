"""Lógica de negocio compartida entre canales de entrada (HTTP, chat, y los
que vengan después). No sabe nada de FastAPI ni de dónde vinieron los datos
— eso es responsabilidad de cada router. Un canal nuevo solo necesita
producir un SolicitudIn válido y llamar a estas funciones."""

from __future__ import annotations

from . import auth
from .github_tracker import GithubTracker, armar_titulo
from .models import SolicitudIn, SolicitudOut


def crear_solicitud(datos: SolicitudIn, rol: auth.Rol, tracker: GithubTracker, redactar_solicitud) -> SolicitudOut:
    """Módulo 1 completo: autoriza, redacta y publica el Issue.

    redactar_solicitud se inyecta (en vez de importar agents.agente_solicitud
    acá) para que este módulo no dependa de la capa de agentes — mantiene la
    misma separación que ya tienen core/state_machine.py y core/auth.py."""
    auth.autorizar_crear(rol)

    descripcion = redactar_solicitud(datos)
    titulo_issue = armar_titulo(datos.titulo, datos.elemento_configuracion)
    issue = tracker.crear_issue(titulo_issue, descripcion)

    return SolicitudOut(clave=issue.clave, url=issue.url, estado=issue.estado)
