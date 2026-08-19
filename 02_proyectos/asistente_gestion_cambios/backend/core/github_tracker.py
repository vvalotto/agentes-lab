"""Wrapper sobre PyGithub — el equivalente a los createJiraIssue /
addCommentToJiraIssue / editJiraIssue / transitionJiraIssue de la skill
original, pero contra Issues de GitHub.

Diferencia clave de diseño frente a Jira: acá no hay workflow que valide
transiciones, así que el estado se modela como label `estado:*` y quien
llama (los routers) es responsable de haber validado la transición con
`core.state_machine` ANTES de invocar `set_estado`. Este módulo no valida
nada de negocio — solo aplica cambios en GitHub.
"""

from __future__ import annotations

from dataclasses import dataclass

from github import Github
from github.Issue import Issue

from . import state_machine


def armar_titulo(titulo_base: str, elemento_configuracion: str, clasificacion: str = "sin clasificar") -> str:
    """Convención de summary del Issue: 'título [EC · clasificación]'."""
    return f"{titulo_base} [{elemento_configuracion} · {clasificacion}]"


def parse_titulo(titulo_completo: str) -> tuple[str, str]:
    """Extrae (titulo_base, elemento_configuracion) de un título armado con
    armar_titulo(). Ignora la clasificación — quien la necesite la lee del
    label clase-*, que es la fuente de verdad."""
    if " [" not in titulo_completo or not titulo_completo.endswith("]"):
        raise ValueError(f"Título no sigue la convención esperada: {titulo_completo!r}")
    titulo_base, resto = titulo_completo.rsplit(" [", 1)
    resto = resto[:-1]
    elemento_configuracion, _, _clasificacion = resto.partition(" · ")
    return titulo_base, elemento_configuracion


@dataclass(frozen=True)
class IssueCambio:
    clave: str  # número de Issue como string, ej. "42"
    url: str
    titulo: str
    descripcion: str
    estado: str  # estado interno (snake_case), leído desde el label estado:*
    labels: list[str]


class GithubTracker:
    def __init__(self, token: str, repo_full_name: str):
        self._client = Github(token)
        self._repo = self._client.get_repo(repo_full_name)

    def crear_issue(self, titulo: str, descripcion: str) -> IssueCambio:
        label_inicial = state_machine.label_de_estado(state_machine.ESTADO_INICIAL)
        issue = self._repo.create_issue(
            title=titulo,
            body=descripcion,
            labels=[label_inicial],
        )
        return self._a_issue_cambio(issue)

    def obtener_issue(self, clave: str) -> IssueCambio:
        issue = self._repo.get_issue(int(clave))
        return self._a_issue_cambio(issue)

    def comentar(self, clave: str, comentario: str) -> None:
        issue = self._repo.get_issue(int(clave))
        issue.create_comment(comentario)

    def set_estado(self, clave: str, estado_nuevo: str) -> None:
        """Reemplaza el label estado:* actual por el del estado nuevo.

        No valida si la transición es legal — eso ya lo hizo
        state_machine.transicionar() antes de llamar acá.
        """
        issue = self._repo.get_issue(int(clave))
        labels_sin_estado = [
            label.name for label in issue.labels if state_machine.estado_de_label(label.name) is None
        ]
        nuevo_label = state_machine.label_de_estado(estado_nuevo)
        issue.set_labels(*labels_sin_estado, nuevo_label)

    def set_clase_y_titulo(self, clave: str, clase: str) -> None:
        """Aplica el label clase-* y actualiza el summary con la clasificación
        definitiva, tal como hacía el Módulo 2 en editJiraIssue (la clase no
        se conoce al crear el Issue, solo al aprobarlo). Relee el título
        actual para no depender de que el caller recuerde el EC por su cuenta."""
        issue = self._repo.get_issue(int(clave))
        titulo_base, elemento_configuracion = parse_titulo(issue.title)
        labels_sin_clase = [label.name for label in issue.labels if not label.name.startswith("clase-")]
        label_clase = f"clase-{clase.lower()}"
        issue.set_labels(*labels_sin_clase, label_clase)
        nuevo_titulo = f"{titulo_base} [{elemento_configuracion} · Clase {clase}]"
        issue.edit(title=nuevo_titulo)

    def _a_issue_cambio(self, issue: Issue) -> IssueCambio:
        estado = None
        nombres_labels = [label.name for label in issue.labels]
        for nombre in nombres_labels:
            posible_estado = state_machine.estado_de_label(nombre)
            if posible_estado is not None:
                estado = posible_estado
                break
        if estado is None:
            raise ValueError(f"El Issue #{issue.number} no tiene ningún label estado:* — no se puede operar sobre él")
        return IssueCambio(
            clave=str(issue.number),
            url=issue.html_url,
            titulo=issue.title,
            descripcion=issue.body or "",
            estado=estado,
            labels=nombres_labels,
        )
