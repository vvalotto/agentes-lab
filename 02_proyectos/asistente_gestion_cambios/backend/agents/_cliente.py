"""Cliente Claude compartido por los mini-agentes de este backend.

Cada "agente" acá es una única llamada a la API con un system prompt
especializado — no un loop ReAct con tools propias (ver Decisión de diseño
#3 del plan: las acciones que necesitan una tool, como crear el Issue o
transicionar estado, las hace el backend directamente contra GitHub, de
forma determinística; el agente solo aporta el juicio de redacción).

stop_reason se maneja explícito: en hola_agente/agente_ddd.py el caso
'max_tokens' cayendo en un else mudo fue un bug real (ver diario
2026-08-06). Acá no se repite: 'max_tokens' devuelve lo generado con una
marca explícita, y cualquier otro stop_reason inesperado levanta un error
en vez de fallar en silencio.
"""

from __future__ import annotations

import anthropic

from .. import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

MODEL = "claude-haiku-4-5-20251001"


class RespuestaInesperadaError(Exception):
    def __init__(self, stop_reason: str):
        self.stop_reason = stop_reason
        super().__init__(f"stop_reason inesperado del modelo: '{stop_reason}'")


def redactar(system_prompt: str, prompt: str, max_tokens: int = 700) -> str:
    response = _client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )

    texto = "".join(block.text for block in response.content if hasattr(block, "text"))

    if response.stop_reason == "end_turn":
        return texto
    if response.stop_reason == "max_tokens":
        return texto + "\n\n*(redacción truncada por límite de tokens — revisar antes de publicar)*"
    raise RespuestaInesperadaError(response.stop_reason)


def extraer(system_prompt: str, prompt: str, tool_schema: dict, max_tokens: int = 500) -> dict:
    """Fuerza al modelo a llamar tool_schema y devuelve sus argumentos.

    A diferencia de redactar(), acá no queremos prosa — queremos datos
    estructurados. tool_choice fuerza la llamada en vez de dejarle al modelo
    la opción de contestar en texto libre."""
    response = _client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        tools=[tool_schema],
        tool_choice={"type": "tool", "name": tool_schema["name"]},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    raise RespuestaInesperadaError(response.stop_reason)
