"""Agente del Módulo 1 (8.2.1 — Solicitud). Redacta la description del
Issue a partir de los datos crudos que manda el frontend, con la
estructura de plantilla_solicitud.md."""

from __future__ import annotations

from pathlib import Path

from ..core.models import SolicitudIn
from ._cliente import redactar

_PLANTILLA = (Path(__file__).resolve().parent.parent / "assets" / "plantilla_solicitud.md").read_text()

_SYSTEM_PROMPT = """Redactás descriptions de solicitudes de cambio de software médico para
gestión de configuración bajo IEC 62304 (cláusula 8.2.1).

Recibís datos crudos de una solicitud y devolvés la description del Issue de GitHub
siguiendo EXACTAMENTE esta estructura de plantilla (rellenando cada campo entre llaves
con prosa clara a partir de los datos recibidos, sin inventar información que no te dieron):

---
{plantilla}
---

Reglas:
- No agregues secciones que no estén en la plantilla.
- No opines sobre si el cambio debería aprobarse — eso es el Módulo 2, no tu trabajo.
- Sé preciso y conciso; esto lo va a leer un aprobador para decidir.
- Devolvé SOLO el contenido final (sin explicar lo que hiciste, sin markdown de código alrededor)."""


def redactar_solicitud(datos: SolicitudIn) -> str:
    prompt = (
        "Datos crudos de la solicitud:\n\n"
        f"- Título: {datos.titulo}\n"
        f"- Elemento de configuración: {datos.elemento_configuracion}\n"
        f"- Origen del reporte: {datos.origen_reporte}\n"
        f"- Solicitante: {datos.solicitante}\n"
        f"- Urgencia: {datos.urgencia}\n"
        f"- Problema/mejora: {datos.descripcion_problema}\n"
        f"- Comportamiento esperado: {datos.comportamiento_esperado}\n"
        f"- Comportamiento observado: {datos.comportamiento_observado}\n"
    )
    system_prompt = _SYSTEM_PROMPT.format(plantilla=_PLANTILLA)
    return redactar(system_prompt, prompt)
