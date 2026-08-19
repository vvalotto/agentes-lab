"""Máquina de estados del flujo de gestión de cambios (IEC 62304 8.2).

En el diseño original (skill sobre Jira) esta validación la hacía gratis el
workflow configurado en Jira: el campo Status solo permite transicionar hacia
los estados que el workflow tiene conectados. Acá no hay workflow — los
estados se modelan como labels `estado:*` sobre el Issue de GitHub, así que
esta tabla es la que impide, por ejemplo, pasar de "pendiente_aprobacion"
directo a "cerrado".
"""

from __future__ import annotations


class TransicionInvalidaError(Exception):
    """El estado actual no admite la acción solicitada."""

    def __init__(self, estado_actual: str, accion: str):
        self.estado_actual = estado_actual
        self.accion = accion
        super().__init__(
            f"No se puede aplicar la acción '{accion}' desde el estado '{estado_actual}'"
        )


PENDIENTE_APROBACION = "pendiente_aprobacion"
APROBADO_PENDIENTE_IMPLEMENTACION = "aprobado_pendiente_implementacion"
RECHAZADO = "rechazado"
IMPLEMENTADO_PENDIENTE_VERIFICACION = "implementado_pendiente_verificacion"
EN_VERIFICACION = "en_verificacion"
CERRADO = "cerrado"
RECHAZADO_PENDIENTE_CORREGIR = "rechazado_pendiente_corregir"

ESTADO_INICIAL = PENDIENTE_APROBACION

ESTADOS_TERMINALES = {RECHAZADO, CERRADO}

# (estado_actual, accion) -> estado_nuevo
TRANSICIONES: dict[tuple[str, str], str] = {
    (PENDIENTE_APROBACION, "aprobar"): APROBADO_PENDIENTE_IMPLEMENTACION,
    (PENDIENTE_APROBACION, "rechazar"): RECHAZADO,
    (APROBADO_PENDIENTE_IMPLEMENTACION, "implementar"): IMPLEMENTADO_PENDIENTE_VERIFICACION,
    (IMPLEMENTADO_PENDIENTE_VERIFICACION, "iniciar_verificacion"): EN_VERIFICACION,
    (EN_VERIFICACION, "cerrar"): CERRADO,
    (EN_VERIFICACION, "rechazar_verificacion"): RECHAZADO_PENDIENTE_CORREGIR,
    (RECHAZADO_PENDIENTE_CORREGIR, "corregir"): IMPLEMENTADO_PENDIENTE_VERIFICACION,
}


def transicionar(estado_actual: str, accion: str) -> str:
    """Devuelve el estado nuevo si la transición es válida.

    Lanza TransicionInvalidaError si no lo es — quien llama debe traducir
    eso a un 409 en el endpoint, nunca aplicar el cambio igual.
    """
    clave = (estado_actual, accion)
    if clave not in TRANSICIONES:
        raise TransicionInvalidaError(estado_actual, accion)
    return TRANSICIONES[clave]


def label_de_estado(estado: str) -> str:
    """Convierte el estado interno (snake_case) al label de GitHub (kebab-case)."""
    return "estado:" + estado.replace("_", "-")


def estado_de_label(label: str) -> str | None:
    """Inverso de label_de_estado, para leer el estado actual desde los labels del Issue."""
    if not label.startswith("estado:"):
        return None
    return label[len("estado:") :].replace("-", "_")
