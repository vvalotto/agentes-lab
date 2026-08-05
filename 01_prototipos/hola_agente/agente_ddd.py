#!/usr/bin/env python3
"""
Agente DDD — Prototipo: hola_agente
====================================
Autor: Víctor Valotto (laboratorio personal)
Etapa: 2 — Primer agente funcional

Demuestra el ciclo ReAct (Razonar → Actuar → Observar) usando
la API de Claude con tool use.

Dado un concepto de DDD, el agente produce:
  1. Una definición en estilo narrativo con metáfora y ejemplo
  2. Una pregunta socrática para usar en clase
  3. Un fragmento de código Python pedagógico

Estructura del archivo (leerlo de arriba hacia abajo):
  1. Cliente API
  2. Esquema de herramientas  → lo que el MODELO ve y puede pedir
  3. Implementación de tools  → lo que el CÓDIGO ejecuta realmente
  4. El ciclo ReAct           → el corazón del agente
  5. Ejecución principal
"""

import os
import anthropic
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
# 1. CLIENTE
# ─────────────────────────────────────────────────────────────
# La API key se lee de la variable de entorno ANTHROPIC_API_KEY,
# cargada desde el archivo .env en la raíz del proyecto (ver .env.example).

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Podés cambiar el modelo según velocidad/costo deseado:
#   claude-haiku-4-5-20251001  → rápido y económico, ideal para pruebas
#   claude-sonnet-4-6          → mejor calidad, más lento
MODEL = "claude-haiku-4-5-20251001"


# ─────────────────────────────────────────────────────────────
# 2. ESQUEMA DE HERRAMIENTAS
#    Esto es lo que el modelo VE: nombres, descripciones y parámetros.
#    El modelo NO ejecuta código. Solo declara "quiero usar esta tool
#    con estos argumentos". El loop ReAct ejecuta la función real.
# ─────────────────────────────────────────────────────────────

TOOLS_SCHEMA = [
    {
        "name": "generar_definicion",
        "description": (
            "Genera una definición del concepto DDD solicitado. "
            "Incluye: explicación técnica precisa, una metáfora del mundo real "
            "y un ejemplo concreto de aplicación en un sistema de software."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concepto": {
                    "type": "string",
                    "description": "El concepto DDD a definir. Ej: 'Agregado', 'Entidad', 'Value Object'"
                }
            },
            "required": ["concepto"]
        }
    },
    {
        "name": "crear_pregunta_socratica",
        "description": (
            "Crea una pregunta socrática sobre el concepto DDD, diseñada para "
            "generar reflexión en estudiantes universitarios de ingeniería de software. "
            "La pregunta no tiene respuesta obvia y conecta el concepto con "
            "decisiones de diseño reales."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concepto": {
                    "type": "string",
                    "description": "El concepto DDD sobre el que crear la pregunta socrática"
                }
            },
            "required": ["concepto"]
        }
    },
    {
        "name": "generar_codigo",
        "description": (
            "Genera un fragmento de código Python (15-25 líneas) que ilustra el concepto DDD. "
            "El código es pedagógico: nombres descriptivos, comentarios clave, "
            "sin dependencias externas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concepto": {
                    "type": "string",
                    "description": "El concepto DDD a ilustrar"
                },
                "dominio": {
                    "type": "string",
                    "description": "Dominio de negocio para el ejemplo. Ej: 'biblioteca', 'hospital', 'e-commerce'"
                }
            },
            "required": ["concepto", "dominio"]
        }
    }
]


# ─────────────────────────────────────────────────────────────
# 3. IMPLEMENTACIÓN DE HERRAMIENTAS
#    Esto es lo que el CÓDIGO ejecuta cuando el modelo pide una tool.
#    Aquí cada función llama a Claude con un prompt específico.
#    En prototipos más avanzados, estas funciones podrían leer
#    archivos de Obsidian, consultar una base de datos, etc.
# ─────────────────────────────────────────────────────────────

def _llamar_claude(prompt: str, max_tokens: int = 500) -> str:
    """Helper interno: llama a Claude con un prompt simple y retorna el texto."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def generar_definicion(concepto: str) -> str:
    prompt = (
        f"Definí el concepto DDD '{concepto}' con este formato exacto:\n\n"
        f"**Definición técnica:** [2-3 oraciones precisas]\n\n"
        f"**Metáfora:** [Una analogía del mundo real que lo haga intuitivo]\n\n"
        f"**Ejemplo:** [Aplicación concreta en un sistema de software]\n\n"
        f"Sé conciso. Máximo 150 palabras en total."
    )
    return _llamar_claude(prompt, max_tokens=400)


def crear_pregunta_socratica(concepto: str) -> str:
    prompt = (
        f"Creá UNA sola pregunta socrática sobre '{concepto}' en Domain-Driven Design. "
        f"Características:\n"
        f"- No tiene respuesta obvia ni única\n"
        f"- Obliga a pensar en trade-offs de diseño\n"
        f"- Es relevante para decisiones reales en proyectos de software\n"
        f"- Está formulada para estudiantes universitarios de ingeniería\n\n"
        f"Solo la pregunta, sin explicación."
    )
    return _llamar_claude(prompt, max_tokens=150)


def generar_codigo(concepto: str, dominio: str) -> str:
    prompt = (
        f"Generá un fragmento de código Python (15-25 líneas) que ilustre '{concepto}' en DDD.\n"
        f"Usá el dominio de '{dominio}'.\n"
        f"Requisitos:\n"
        f"- Nombres de clases y métodos que reflejen el dominio (no genéricos)\n"
        f"- Comentarios que expliquen el 'por qué', no el 'qué'\n"
        f"- Sin imports externos (solo stdlib si es necesario)\n"
        f"- Solo el código, sin explicación antes ni después"
    )
    return _llamar_claude(prompt, max_tokens=600)


# Dispatcher: traduce el nombre de herramienta que pide el modelo
# en la función Python correspondiente. Es el "pegamento" del sistema.
TOOLS_IMPL = {
    "generar_definicion":     lambda args: generar_definicion(args["concepto"]),
    "crear_pregunta_socratica": lambda args: crear_pregunta_socratica(args["concepto"]),
    "generar_codigo":         lambda args: generar_codigo(args["concepto"], args.get("dominio", "e-commerce")),
}


# ─────────────────────────────────────────────────────────────
# 4. EL CICLO ReAct
#    Razonar → Actuar → Observar → (repetir si hace falta) → Respuesta
#
#    Este es el corazón del agente. Lo que hace es simple:
#      a) Llama al modelo con el historial actual
#      b) Si el modelo pide una tool → la ejecuta y agrega el resultado
#      c) Si el modelo termina → retorna la respuesta final
#      d) Repite hasta llegar a (c)
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sos un asistente especializado en Domain-Driven Design (DDD) con estilo pedagógico.

Cuando te pidan explicar un concepto DDD, seguís este proceso en orden:
1. Llamás a generar_definicion() con el concepto
2. Llamás a crear_pregunta_socratica() con el mismo concepto
3. Llamás a generar_codigo() con el concepto y un dominio apropiado que vos elegís
4. Integrás los tres resultados en una respuesta clara y cohesiva

Siempre usás las tres herramientas. Nunca respondés sin haberlas llamado."""


def react_loop(concepto_ddd: str) -> str:
    """
    El ciclo ReAct: mantiene el historial y ejecuta tools hasta que
    el modelo decide que terminó (stop_reason == "end_turn").

    Args:
        concepto_ddd: El concepto DDD a explicar

    Returns:
        La respuesta final integrada del agente
    """
    print(f"\n{'═' * 58}")
    print(f"  AGENTE DDD — Concepto: {concepto_ddd}")
    print(f"{'═' * 58}\n")

    # El historial es la "memoria de corto plazo" del agente.
    # Cada ciclo agrega: respuesta del modelo + resultados de tools.
    messages = [
        {"role": "user", "content": f"Explicame el concepto DDD: {concepto_ddd}"}
    ]

    ciclo = 0

    # ── LOOP ReAct ──────────────────────────────────────────
    while True:
        ciclo += 1
        print(f"[Ciclo {ciclo}] RAZONANDO — consultando al modelo...")

        # El modelo razona y decide su próximo paso
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS_SCHEMA,
            messages=messages
        )

        # ── ACTUAR: el modelo pidió usar herramientas ────────
        if response.stop_reason == "tool_use":

            # Guardamos la respuesta del modelo en el historial
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    nombre = block.name
                    args   = block.input

                    print(f"[Ciclo {ciclo}] ACTUANDO  — {nombre}({args})")

                    # Ejecutamos la función Python correspondiente
                    resultado = TOOLS_IMPL[nombre](args)

                    print(f"[Ciclo {ciclo}] OBSERVANDO — {nombre} devolvió {len(resultado)} chars\n")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,   # el modelo usa este ID para correlacionar
                        "content": resultado
                    })

            # Los resultados vuelven al modelo como mensaje "user"
            # (así funciona el protocolo de tool use en Claude)
            messages.append({"role": "user", "content": tool_results})

        # ── RESPUESTA FINAL: el modelo terminó ───────────────
        elif response.stop_reason == "end_turn":
            print(f"[Ciclo {ciclo}] RESPUESTA FINAL generada luego de {ciclo} ciclos\n")
            print(f"{'─' * 58}\n")

            # Extraemos el texto de la respuesta
            texto_final = ""
            for block in response.content:
                if hasattr(block, "text"):
                    texto_final += block.text

            return texto_final

        # ── CASO INESPERADO ──────────────────────────────────
        else:
            print(f"[!] Stop reason inesperado: {response.stop_reason}")
            break

    return "El agente no pudo completar la tarea."


# ─────────────────────────────────────────────────────────────
# 5. EJECUCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Conceptos que podés probar:
    # "Entidad", "Value Object", "Repositorio",
    # "Evento de Dominio", "Contexto Delimitado", "Servicio de Dominio"

    concepto = "Agregado"

    resultado = react_loop(concepto)
    print(resultado)
