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
    "Cliente del backend multi-agente. Módulo 1 (Solicitud, por formulario, chat o mail) "
    "y Módulo 2 (Aprobación) — los Issues quedan en el repo GitHub dedicado del POC."
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

tab_solicitud, tab_chat, tab_mail, tab_aprobacion = st.tabs(
    ["Módulo 1 — Solicitud", "Chat — Solicitud", "Mail — Solicitud", "Módulo 2 — Aprobación"]
)

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

with tab_chat:
    st.write(
        "Contale el problema como si se lo explicaras a un colega — el agente va "
        "preguntando lo que le falte hasta poder registrar la solicitud."
    )

    if "chat_conversacion_id" not in st.session_state:
        st.session_state.chat_conversacion_id = None
    if "chat_historial_visible" not in st.session_state:
        st.session_state.chat_historial_visible = []
    if "chat_completado" not in st.session_state:
        st.session_state.chat_completado = False

    if st.button("Nueva conversación", key="chat_reset"):
        st.session_state.chat_conversacion_id = None
        st.session_state.chat_historial_visible = []
        st.session_state.chat_completado = False
        st.rerun()

    for mensaje in st.session_state.chat_historial_visible:
        with st.chat_message(mensaje["role"]):
            st.write(mensaje["content"])

    mensaje_usuario = st.chat_input(
        "Escribí acá...", disabled=st.session_state.chat_completado
    )

    if mensaje_usuario:
        st.session_state.chat_historial_visible.append({"role": "user", "content": mensaje_usuario})

        payload = {
            "conversacion_id": st.session_state.chat_conversacion_id,
            "mensaje": mensaje_usuario,
        }
        try:
            resp = requests.post(
                f"{API_BASE_URL}/chat/mensaje",
                json=payload,
                headers={"X-Api-Key": api_key},
                timeout=30,
            )
        except requests.ConnectionError:
            respuesta_asistente = f"No se pudo conectar a {API_BASE_URL} — ¿está corriendo el backend?"
        else:
            if resp.status_code == 200:
                datos = resp.json()
                st.session_state.chat_conversacion_id = datos["conversacion_id"]
                respuesta_asistente = datos["respuesta"]
                if datos.get("solicitud"):
                    st.session_state.chat_completado = True
            else:
                respuesta_asistente = f"{resp.status_code}: {resp.json().get('detail', resp.text)}"

        st.session_state.chat_historial_visible.append({"role": "assistant", "content": respuesta_asistente})
        st.rerun()

with tab_mail:
    st.write(
        "Elegí un mail de la etiqueta configurada del buzón y el agente arranca la "
        "conversación con su contenido — si falta algo, lo pregunta acá mismo, igual "
        "que en el chat manual."
    )

    for clave, valor in {
        "mail_conversacion_id": None,
        "mail_historial_visible": [],
        "mail_completado": False,
        "mail_correos": None,
    }.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor

    if st.button("Nueva conversación", key="mail_reset"):
        st.session_state.mail_conversacion_id = None
        st.session_state.mail_historial_visible = []
        st.session_state.mail_completado = False
        st.session_state.mail_correos = None
        st.session_state.pop("mail_pendiente", None)
        st.rerun()

    mail_iniciado = bool(st.session_state.mail_conversacion_id or st.session_state.mail_historial_visible)

    if not mail_iniciado:
        if st.button("Actualizar bandeja", key="mail_listar"):
            try:
                resp = requests.get(
                    f"{API_BASE_URL}/mail/recientes", headers={"X-Api-Key": api_key}, timeout=30
                )
            except requests.ConnectionError:
                st.error(f"No se pudo conectar a {API_BASE_URL} — ¿está corriendo el backend?")
            else:
                if resp.status_code == 200:
                    st.session_state.mail_correos = resp.json()
                else:
                    st.error(f"{resp.status_code}: {resp.json().get('detail', resp.text)}")

        if st.session_state.mail_correos is not None:
            if not st.session_state.mail_correos:
                st.info("No hay correos en la etiqueta configurada todavía.")
            for correo in st.session_state.mail_correos:
                with st.container(border=True):
                    st.write(f"**{correo['asunto']}**")
                    st.caption(f"{correo['remitente']} — {correo['fecha']}")
                    if st.button("Usar este mail", key=f"usar_{correo['uid']}"):
                        try:
                            resp = requests.get(
                                f"{API_BASE_URL}/mail/{correo['uid']}",
                                headers={"X-Api-Key": api_key},
                                timeout=30,
                            )
                        except requests.ConnectionError:
                            st.error(f"No se pudo conectar a {API_BASE_URL}")
                        else:
                            if resp.status_code == 200:
                                st.session_state.mail_pendiente = resp.json()["contenido"]
                                st.rerun()
                            else:
                                st.error(f"{resp.status_code}: {resp.json().get('detail', resp.text)}")

    mensaje_desde_mail = st.session_state.pop("mail_pendiente", None)

    for mensaje in st.session_state.mail_historial_visible:
        with st.chat_message(mensaje["role"]):
            st.write(mensaje["content"])

    mensaje_usuario = mensaje_desde_mail
    if mail_iniciado and mensaje_usuario is None:
        mensaje_usuario = st.chat_input(
            "Escribí acá si el agente te pregunta algo más...",
            disabled=st.session_state.mail_completado,
            key="mail_chat_input",
        )

    if mensaje_usuario:
        etiqueta_visible = mensaje_usuario if mensaje_desde_mail is None else f"📧 {mensaje_usuario}"
        st.session_state.mail_historial_visible.append({"role": "user", "content": etiqueta_visible})

        payload = {"conversacion_id": st.session_state.mail_conversacion_id, "mensaje": mensaje_usuario}
        try:
            resp = requests.post(
                f"{API_BASE_URL}/chat/mensaje", json=payload, headers={"X-Api-Key": api_key}, timeout=30
            )
        except requests.ConnectionError:
            respuesta_asistente = f"No se pudo conectar a {API_BASE_URL} — ¿está corriendo el backend?"
        else:
            if resp.status_code == 200:
                datos = resp.json()
                st.session_state.mail_conversacion_id = datos["conversacion_id"]
                respuesta_asistente = datos["respuesta"]
                if datos.get("solicitud"):
                    st.session_state.mail_completado = True
            else:
                respuesta_asistente = f"{resp.status_code}: {resp.json().get('detail', resp.text)}"

        st.session_state.mail_historial_visible.append({"role": "assistant", "content": respuesta_asistente})
        st.rerun()

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
