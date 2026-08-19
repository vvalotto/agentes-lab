"""Agente de extracción — canal chat, previo al Módulo 1 (8.2.1).

Es el inverso de agente_solicitud: ese recibe datos limpios y devuelve
prosa; este recibe prosa suelta (los mensajes del usuario en el chat) y
devuelve datos limpios — el mismo shape que espera SolicitudIn. Una vez que
la extracción está completa, el resto del pipeline (agente_solicitud,
github_tracker) no cambia en nada.

Dos llamadas acotadas por turno, no un loop abierto:
  1. extraer_campos()          — tool-use forzado, siempre se llama.
  2. preguntar_por_faltantes() — solo si SolicitudIn todavía no valida."""

from __future__ import annotations

from ._cliente import extraer, redactar

CAMPOS = [
    "titulo",
    "descripcion_problema",
    "elemento_configuracion",
    "comportamiento_esperado",
    "comportamiento_observado",
    "urgencia",
    "origen_reporte",
    "solicitante",
]

ETIQUETAS = {
    "titulo": "un título corto para el cambio",
    "descripcion_problema": "en qué consiste el problema o la mejora",
    "elemento_configuracion": "qué elemento o módulo del sistema está afectado",
    "comportamiento_esperado": "cómo debería comportarse",
    "comportamiento_observado": "cómo se está comportando hoy",
    "urgencia": "qué tan urgente es (rutinaria, significativa, o crítica para la seguridad)",
    "origen_reporte": "de dónde surge el reporte (quién lo detectó o cómo)",
    "solicitante": "el nombre de quien pide el cambio",
}

_TOOL_SCHEMA = {
    "name": "registrar_campos",
    "description": (
        "Registra los datos de una solicitud de cambio de software médico extraídos "
        "de la conversación hasta ahora. Usá '' (string vacío) para cualquier campo "
        "que la conversación todavía no haya mencionado — no inventes valores."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "titulo": {"type": "string"},
            "descripcion_problema": {"type": "string"},
            "elemento_configuracion": {"type": "string"},
            "comportamiento_esperado": {"type": "string"},
            "comportamiento_observado": {"type": "string"},
            "urgencia": {
                "type": "string",
                "enum": ["", "rutinaria", "significativa", "critica_para_seguridad"],
            },
            "origen_reporte": {"type": "string"},
            "solicitante": {"type": "string"},
        },
        "required": CAMPOS,
    },
}

_SYSTEM_EXTRAER = """Extraés datos de solicitudes de cambio de software médico (IEC 62304, cláusula
8.2.1) a partir de una conversación libre con el solicitante.

Se te da la transcripción completa de sus mensajes hasta ahora, en orden. Llamá a
registrar_campos con el mejor valor conocido para cada campo, combinando información de
TODOS los mensajes (no solo el último). Si un campo no se mencionó en ningún mensaje,
usá '' — nunca inventes ni asumas un valor razonable, aunque parezca obvio."""


def extraer_campos(historial: list[str]) -> dict:
    transcripcion = "\n".join(f"- {mensaje}" for mensaje in historial)
    prompt = f"Mensajes del solicitante hasta ahora:\n\n{transcripcion}"
    return extraer(_SYSTEM_EXTRAER, prompt, _TOOL_SCHEMA)


_SYSTEM_PREGUNTAR = """Sos parte de un chat que junta datos para una solicitud de cambio de
software médico (IEC 62304 8.2.1). Ya tenés algunos datos; faltan otros.

Escribí UNA sola pregunta corta y conversacional (no una lista, no numerada) pidiendo lo
que falta — priorizá el campo más importante para entender el problema si falta más de
uno. Tono directo y humano, como si fueras una persona del equipo de calidad, no un
formulario. No repitas lo que ya se sabe, no agradezcas ni saludes, andá directo a la
pregunta."""


def preguntar_por_faltantes(campos_conocidos: dict, campos_faltantes: list[str]) -> str:
    conocido_fmt = "\n".join(
        f"- {clave}: {valor}" for clave, valor in campos_conocidos.items() if valor
    ) or "(nada todavía)"
    faltante_fmt = "\n".join(f"- {ETIQUETAS.get(c, c)}" for c in campos_faltantes)
    prompt = (
        f"Datos ya conocidos:\n{conocido_fmt}\n\n"
        f"Falta preguntar por:\n{faltante_fmt}"
    )
    return redactar(_SYSTEM_PREGUNTAR, prompt, max_tokens=150)
