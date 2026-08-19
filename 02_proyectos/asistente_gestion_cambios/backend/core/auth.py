"""Autorización por rol — el límite de sistema que en la skill original era una
instrucción de prompt ("preguntá el rol y confiá en la respuesta").

Acá el rol no lo dice quien llama: lo determina la API key que manda en el
header `X-Api-Key`, resuelta contra un mapeo que carga `config.py` desde el
entorno. Un endpoint nunca debe aceptar el rol como parámetro del body.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rol:
    nombre: str
    puede_crear: bool
    clases_que_aprueba: frozenset[str]  # subconjunto de {"A", "B", "C"}


# Misma tabla de la skill original (gestion-cambios-iec62304-8-2).
ROLES: dict[str, Rol] = {
    "arquitecto_software": Rol(
        nombre="Arquitecto de Software",
        puede_crear=True,
        clases_que_aprueba=frozenset({"A", "B", "C"}),
    ),
    "quality_manager": Rol(
        nombre="Quality Manager / Responsable de Calidad",
        puede_crear=True,
        clases_que_aprueba=frozenset({"A"}),
    ),
    "director_tecnico": Rol(
        nombre="Director Técnico",
        puede_crear=True,
        clases_que_aprueba=frozenset({"A", "B"}),
    ),
    "lider_desarrollo": Rol(
        nombre="Líder de Desarrollo",
        puede_crear=True,
        clases_que_aprueba=frozenset({"B", "C"}),
    ),
    "usuario_clinico": Rol(
        nombre="Usuario clínico / Ingeniero biomédico",
        puede_crear=True,
        clases_que_aprueba=frozenset(),
    ),
}


class ApiKeyInvalidaError(Exception):
    """La API key no resuelve a ningún rol conocido."""


class NoAutorizadoError(Exception):
    """El rol resuelto no tiene permiso para la acción solicitada."""

    def __init__(self, rol: Rol, accion: str):
        self.rol = rol
        self.accion = accion
        super().__init__(f"El rol '{rol.nombre}' no está autorizado a: {accion}")


def resolver_rol(api_key: str, roles_api_keys: dict[str, str]) -> Rol:
    """api_key -> Rol, usando el mapeo cargado por config.py desde el entorno."""
    clave_rol = roles_api_keys.get(api_key)
    if clave_rol is None or clave_rol not in ROLES:
        raise ApiKeyInvalidaError()
    return ROLES[clave_rol]


def autorizar_crear(rol: Rol) -> None:
    if not rol.puede_crear:
        raise NoAutorizadoError(rol, "crear solicitud de cambio")


def autorizar_aprobar(rol: Rol, clase: str) -> None:
    if clase not in rol.clases_que_aprueba:
        raise NoAutorizadoError(rol, f"aprobar cambios de clase {clase}")
