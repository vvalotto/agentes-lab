"""Agente del Módulo 2 (8.2.1 — Aprobación). Redacta el comentario de
análisis de impacto a partir de las notas del aprobador, con la
estructura de plantilla_aprobacion.md.

Importante: este agente NUNCA decide si el cambio se aprueba ni valida la
autorización del rol — eso ya pasó en el router (core.auth) antes de
llegar acá. El agente solo redacta lo que el aprobador ya decidió."""

from __future__ import annotations

from pathlib import Path

from ..core.models import AprobacionIn
from ._cliente import redactar

_PLANTILLA = (Path(__file__).resolve().parent.parent / "assets" / "plantilla_aprobacion.md").read_text()

_SYSTEM_PROMPT = """Redactás comentarios de análisis de impacto y decisión de aprobación para
solicitudes de cambio de software médico bajo IEC 62304 (cláusula 8.2.1).

Recibís la decisión ya tomada por una persona autorizada y sus notas, y devolvés el
comentario del Issue de GitHub siguiendo EXACTAMENTE esta estructura de plantilla:

---
{plantilla}
---

Reglas:
- La decisión y la clasificación ya están tomadas — tu trabajo es redactar, no decidir.
- No cambies ni suavices la decisión que te dieron.
- No inventes impacto en otros elementos ni pruebas de regresión que no te dieron;
  si vino vacío, escribí "No se identificó impacto adicional" o "No se sugirieron
  pruebas adicionales" según corresponda.
- Devolvé SOLO el contenido final (sin explicar lo que hiciste, sin markdown de código alrededor)."""


def redactar_aprobacion(datos: AprobacionIn) -> str:
    prompt = (
        "Notas del aprobador:\n\n"
        f"- Decisión: {datos.decision}\n"
        f"- Clasificación IEC 62304: Clase {datos.clase}\n"
        f"- Aprobador: {datos.aprobador}\n"
        f"- Justificación: {datos.justificacion}\n"
        f"- Impacto en otros elementos de configuración: {datos.impacto_otros_elementos or '(no indicado)'}\n"
        f"- Pruebas de regresión sugeridas: {datos.pruebas_regresion_sugeridas or '(no indicado)'}\n"
    )
    system_prompt = _SYSTEM_PROMPT.format(plantilla=_PLANTILLA)
    return redactar(system_prompt, prompt)
