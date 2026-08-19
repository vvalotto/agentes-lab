"""FastAPI app — backend multi-agente de gestión de cambios IEC 62304 8.2.

POC: Módulos 1 (Solicitud, por formulario y por chat) y 2 (Aprobación).
Implementación, Verificación y Trazabilidad quedan para después de validar
este patrón (ver README del proyecto)."""

from __future__ import annotations

from fastapi import FastAPI

from .routers import aprobaciones, chat, solicitudes

app = FastAPI(
    title="Gestión de Cambios IEC 62304 8.2 — backend multi-agente (POC)",
    version="0.1.0",
)

app.include_router(solicitudes.router, tags=["Módulo 1 — Solicitud"])
app.include_router(chat.router, tags=["Módulo 1 — Solicitud (chat)"])
app.include_router(aprobaciones.router, tags=["Módulo 2 — Aprobación"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
