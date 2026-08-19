"""Esquemas de entrada/salida de la API. Los nombres de campo siguen los
datos que el Módulo 1 y el Módulo 2 de la skill original recopilaban con el
usuario en conversación — acá los manda el frontend en un solo request."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Urgencia = Literal["rutinaria", "significativa", "critica_para_seguridad"]
Decision = Literal["aprobado", "aprobado_con_condiciones", "rechazado"]
Clase = Literal["A", "B", "C"]


class SolicitudIn(BaseModel):
    titulo: str = Field(..., description="Título corto del cambio propuesto")
    descripcion_problema: str = Field(..., description="Problema o mejora, en palabras del solicitante")
    elemento_configuracion: str = Field(..., description="EC afectado, ej. 'Módulo de Análisis Cardíaco'")
    comportamiento_esperado: str
    comportamiento_observado: str
    urgencia: Urgencia
    origen_reporte: str = Field(..., description="De dónde surge: auditoría, usuario, monitoreo, etc.")
    solicitante: str


class SolicitudOut(BaseModel):
    clave: str  # ej. "42" (número de Issue) — no hay prefijo tipo CM82- en GitHub
    url: str
    estado: str


class AprobacionIn(BaseModel):
    decision: Decision
    clase: Clase = Field(..., description="Clasificación IEC 62304 definitiva del cambio")
    justificacion: str
    impacto_otros_elementos: str = Field("", description="Otros EC potencialmente afectados")
    pruebas_regresion_sugeridas: str = Field("", description="Qué pruebas de regresión hacen falta")
    aprobador: str


class AprobacionOut(BaseModel):
    clave: str
    estado_nuevo: str
    decision: Decision


class MensajeChatIn(BaseModel):
    conversacion_id: str | None = Field(None, description="None para arrancar una conversación nueva")
    mensaje: str


class MensajeChatOut(BaseModel):
    conversacion_id: str
    respuesta: str
    solicitud: SolicitudOut | None = Field(None, description="Presente solo cuando la solicitud ya se creó")
