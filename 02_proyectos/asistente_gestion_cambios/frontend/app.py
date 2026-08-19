"""Frontend Streamlit — POC del backend multi-agente de gestión de cambios.

No habla con Claude ni con GitHub directamente: es un cliente puro de la
API (backend/main.py). El punto que este POC quiere demostrar — que la
autorización por rol vive en la API, no en el prompt — se ve acá: el
campo "API key" simula distintos usuarios, y el backend es el que decide
si esa key puede crear o aprobar, no este formulario.
"""

import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8731")

st.set_page_config(page_title="Gestión de Cambios IEC 62304 8.2 — POC", layout="centered")
st.title("Gestión de Cambios IEC 62304 · 8.2 (POC)")
st.caption(
    "Cliente del backend multi-agente. Módulo 1 (Solicitud) y Módulo 2 (Aprobación) — "
    "los Issues quedan en el repo GitHub dedicado del POC."
)

with st.sidebar:
    st.subheader("Identidad de prueba")
    api_key = st.text_input(
        "API key",
        value="dev-arquitecto",
        help=(
            "Simula distintos roles. Claves disponibles en el .env del backend: "
            "dev-arquitecto (Arquitecto de Software), dev-lider (Líder de Desarrollo), "
            "dev-clinico (Usuario clínico). El backend decide qué puede hacer cada una — "
            "este campo no le dice nada al servidor sobre el rol, solo la key."
        ),
    )
    st.caption(f"API: {API_BASE_URL}")

tab_solicitud, tab_aprobacion = st.tabs(["Módulo 1 — Solicitud", "Módulo 2 — Aprobación"])

with tab_solicitud:
    st.write("Registrá una solicitud de cambio. El agente redacta la description del Issue.")
    with st.form("form_solicitud"):
        titulo = st.text_input("Título corto")
        elemento_configuracion = st.text_input("Elemento de configuración afectado")
        descripcion_problema = st.text_area("Problema o mejora propuesta")
        comportamiento_esperado = st.text_area("Comportamiento esperado")
        comportamiento_observado = st.text_area("Comportamiento observado")
        urgencia = st.selectbox("Urgencia", ["rutinaria", "significativa", "critica_para_seguridad"])
        origen_reporte = st.text_input("Origen del reporte")
        solicitante = st.text_input("Solicitante")
        enviado = st.form_submit_button("Crear solicitud")

    if enviado:
        payload = {
            "titulo": titulo,
            "elemento_configuracion": elemento_configuracion,
            "descripcion_problema": descripcion_problema,
            "comportamiento_esperado": comportamiento_esperado,
            "comportamiento_observado": comportamiento_observado,
            "urgencia": urgencia,
            "origen_reporte": origen_reporte,
            "solicitante": solicitante,
        }
        try:
            resp = requests.post(
                f"{API_BASE_URL}/solicitudes",
                json=payload,
                headers={"X-Api-Key": api_key},
                timeout=30,
            )
        except requests.ConnectionError:
            st.error(f"No se pudo conectar a {API_BASE_URL} — ¿está corriendo el backend (uvicorn backend.main:app)?")
        else:
            if resp.status_code == 201:
                datos = resp.json()
                st.success(f"Issue creado: {datos['clave']} — estado: {datos['estado']}")
                st.markdown(f"[Ver en GitHub]({datos['url']})")
            else:
                st.error(f"{resp.status_code}: {resp.json().get('detail', resp.text)}")

with tab_aprobacion:
    st.write("Registrá la decisión de aprobación sobre una solicitud existente.")
    with st.form("form_aprobacion"):
        clave = st.text_input("Clave del Issue (número, ej. '2')")
        decision = st.selectbox("Decisión", ["aprobado", "aprobado_con_condiciones", "rechazado"])
        clase = st.selectbox("Clasificación IEC 62304", ["A", "B", "C"])
        justificacion = st.text_area("Justificación")
        impacto_otros_elementos = st.text_area("Impacto en otros elementos de configuración", value="")
        pruebas_regresion_sugeridas = st.text_area("Pruebas de regresión sugeridas", value="")
        aprobador = st.text_input("Aprobador")
        enviado_aprobacion = st.form_submit_button("Registrar decisión")

    if enviado_aprobacion:
        payload = {
            "decision": decision,
            "clase": clase,
            "justificacion": justificacion,
            "impacto_otros_elementos": impacto_otros_elementos,
            "pruebas_regresion_sugeridas": pruebas_regresion_sugeridas,
            "aprobador": aprobador,
        }
        try:
            resp = requests.post(
                f"{API_BASE_URL}/solicitudes/{clave}/aprobacion",
                json=payload,
                headers={"X-Api-Key": api_key},
                timeout=30,
            )
        except requests.ConnectionError:
            st.error(f"No se pudo conectar a {API_BASE_URL} — ¿está corriendo el backend (uvicorn backend.main:app)?")
        else:
            if resp.status_code == 200:
                datos = resp.json()
                st.success(f"Issue {datos['clave']} → estado nuevo: {datos['estado_nuevo']} ({datos['decision']})")
            else:
                st.error(f"{resp.status_code}: {resp.json().get('detail', resp.text)}")
