"""Estado de las conversaciones del canal chat — en memoria, sin persistencia.

Coherente con el resto del backend: es un POC de un solo proceso, y ninguna
otra pieza (github_tracker, state_machine) persiste nada por su cuenta
tampoco — la única fuente de verdad durable es GitHub. Si el proceso se
reinicia, las conversaciones abiertas se pierden y el usuario simplemente
empieza de nuevo — no hay Issues a medio crear que puedan quedar
inconsistentes."""

from __future__ import annotations

import uuid

_conversaciones: dict[str, list[str]] = {}


def nueva_conversacion() -> str:
    conversacion_id = str(uuid.uuid4())
    _conversaciones[conversacion_id] = []
    return conversacion_id


def agregar_mensaje(conversacion_id: str, mensaje: str) -> list[str]:
    if conversacion_id not in _conversaciones:
        _conversaciones[conversacion_id] = []
    _conversaciones[conversacion_id].append(mensaje)
    return _conversaciones[conversacion_id]


def obtener_historial(conversacion_id: str) -> list[str]:
    return _conversaciones.get(conversacion_id, [])


def cerrar_conversacion(conversacion_id: str) -> None:
    _conversaciones.pop(conversacion_id, None)
