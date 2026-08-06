#!/usr/bin/env python3
"""
Agente DDD — Prototipo: hola_agente_sdk
========================================
La misma tarea que 01_prototipos/hola_agente/agente_ddd.py (explicar un
concepto DDD), pero implementada con el Claude Agent SDK en vez de la
API directa.

Diferencia clave frente al prototipo anterior:
  - agente_ddd.py:      el loop ReAct se escribe a mano (while True + tool_use)
  - agente_ddd_sdk.py:  el SDK provee el loop (query()); acá solo se define
                        una tool propia y se conecta vía un servidor MCP
                        en memoria — no hay servidor externo que levantar.

Requiere el Claude Code CLI instalado (el SDK lo invoca como subproceso).
Verificar con: claude --version
"""

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

# ─────────────────────────────────────────────────────────────
# 1. HERRAMIENTA PROPIA
#    A diferencia de hola_agente.py (donde las tools llamaban a
#    Claude internamente), acá la tool es una consulta local —
#    un glosario en memoria. El SDK decide cuándo llamarla y
#    Claude integra el resultado en su respuesta final.
# ─────────────────────────────────────────────────────────────

GLOSARIO_DDD = {
    "agregado": (
        "Cluster de entidades y value objects tratado como una unidad de "
        "consistencia transaccional, con una única raíz (Aggregate Root)."
    ),
    "entidad": (
        "Objeto de dominio definido por su identidad, no por sus atributos. "
        "Dos entidades con los mismos datos pero distinta identidad son distintas."
    ),
    "value object": (
        "Objeto de dominio definido por sus atributos, sin identidad propia. "
        "Dos value objects con los mismos atributos son intercambiables."
    ),
    "repositorio": (
        "Abstracción que simula una colección en memoria de agregados, "
        "ocultando los detalles de persistencia al dominio."
    ),
}


@tool(
    "buscar_termino_ddd",
    "Busca la definición canónica de un término de Domain-Driven Design en el "
    "glosario del laboratorio. Usar esto ANTES de explicar cualquier término "
    "DDD, en vez de responder de memoria.",
    {"termino": str},
)
async def buscar_termino_ddd(args: dict) -> dict:
    termino = args["termino"].strip().lower()
    definicion = GLOSARIO_DDD.get(termino)
    texto = definicion or f"'{termino}' no está en el glosario del laboratorio."
    return {"content": [{"type": "text", "text": texto}]}


# ─────────────────────────────────────────────────────────────
# 2. SERVIDOR MCP EN MEMORIA
#    create_sdk_mcp_server empaqueta la tool en un servidor MCP
#    que corre dentro del mismo proceso Python.
# ─────────────────────────────────────────────────────────────

servidor_ddd = create_sdk_mcp_server(
    name="ddd-glosario",
    version="1.0.0",
    tools=[buscar_termino_ddd],
)


# ─────────────────────────────────────────────────────────────
# 3. OPCIONES DEL AGENTE
#    allowed_tools restringe al agente a SOLO la tool del glosario:
#    sin acceso a filesystem, bash, ni al resto del harness de
#    Claude Code. Es la diferencia clave frente a usar Claude Code
#    directamente — acá se decide exactamente qué puede tocar.
# ─────────────────────────────────────────────────────────────

opciones = ClaudeAgentOptions(
    system_prompt=(
        "Sos un asistente DDD para docencia universitaria. Cuando te pidan "
        "explicar un término, consultá SIEMPRE la tool buscar_termino_ddd "
        "primero, y después elaborá con una metáfora y un ejemplo de código "
        "Python (15-25 líneas, nombres del dominio, sin dependencias externas)."
    ),
    mcp_servers={"ddd": servidor_ddd},
    allowed_tools=["mcp__ddd__buscar_termino_ddd"],
    max_turns=5,
)


# ─────────────────────────────────────────────────────────────
# 4. EJECUCIÓN
#    query() reemplaza al while True manual de agente_ddd.py: es
#    un generador async que va emitiendo mensajes a medida que el
#    agente razona, llama tools y responde.
# ─────────────────────────────────────────────────────────────

async def explicar_concepto(concepto: str) -> None:
    print(f"\n{'═' * 58}")
    print(f"  AGENTE DDD (SDK) — Concepto: {concepto}")
    print(f"{'═' * 58}\n")

    prompt = f"Explicame el concepto DDD: {concepto}"

    async for mensaje in query(prompt=prompt, options=opciones):
        if isinstance(mensaje, AssistantMessage):
            for bloque in mensaje.content:
                if isinstance(bloque, TextBlock):
                    print(bloque.text, end="")
        elif isinstance(mensaje, ResultMessage):
            costo = f"${mensaje.total_cost_usd:.4f}" if mensaje.total_cost_usd else "N/D"
            print(f"\n\n{'─' * 58}")
            print(f"[Sesión finalizada — {mensaje.num_turns} turnos, costo estimado: {costo}]")


if __name__ == "__main__":
    # Conceptos disponibles en el glosario: "Agregado", "Entidad",
    # "Value Object", "Repositorio". Probá también uno que NO esté
    # (ej. "Conformista") para ver cómo reacciona el agente.
    concepto = "Agregado"

    anyio.run(explicar_concepto, concepto)
