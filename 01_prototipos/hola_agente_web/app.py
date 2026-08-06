#!/usr/bin/env python3
"""
Agente DDD — Prototipo: hola_agente_web
=========================================
Misma tarea que hola_agente/agente_ddd.py (explicar un concepto DDD con el
ciclo ReAct), pero con una interfaz de chat en vez de un valor hardcodeado
en el código. El usuario escribe el concepto en el navegador; el ReAct loop
que ya existe no cambia — solo cambia quién dispara el prompt.

Ejecutar con:
  streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st

# hola_agente/ no es un paquete instalado — se agrega su carpeta al path
# para reusar react_loop() sin duplicar el ciclo ReAct.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hola_agente"))
from agente_ddd import react_loop  # noqa: E402

st.set_page_config(page_title="Agente DDD", page_icon="🧩")
st.title("🧩 Agente DDD")
st.caption(
    "Escribí un concepto de Domain-Driven Design (Agregado, Entidad, "
    "Value Object, Repositorio, Evento de Dominio...) y el agente genera "
    "una definición, una pregunta socrática y un ejemplo de código."
)

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

concepto = st.chat_input("¿Qué concepto DDD querés estudiar?")

if concepto:
    st.session_state.mensajes.append({"role": "user", "content": concepto})
    with st.chat_message("user"):
        st.markdown(concepto)

    with st.chat_message("assistant"):
        with st.spinner(f"Razonando sobre '{concepto}'..."):
            respuesta = react_loop(concepto)
        st.markdown(respuesta)

    st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
