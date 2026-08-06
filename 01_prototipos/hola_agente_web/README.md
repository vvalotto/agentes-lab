# hola_agente_web — Interfaz de chat para el agente DDD

> Misma tarea que `hola_agente/`, con una interfaz de chat (Streamlit) en
> vez de un concepto hardcodeado en el código. El ciclo ReAct no cambia —
> se reusa `react_loop()` tal cual está.

**Etapa:** 2 — Primer agente funcional (iteración de interfaz)
**Estado:** completo
**Tiempo estimado para ejecutarlo:** 5 minutos

---

## Qué hace

El usuario escribe un concepto DDD en un chat web. El agente corre el
mismo ciclo ReAct de `hola_agente/agente_ddd.py` (razonar → tool use →
observar) y devuelve la respuesta en el chat.

## Cómo ejecutarlo

```bash
cd /Users/victor/PycharmProjects/agentes-lab
source .venv/bin/activate
pip install -r requirements.txt   # instala streamlit si falta

cd 01_prototipos/hola_agente_web
streamlit run app.py
```

Requiere `ANTHROPIC_API_KEY` en `.env` (mismo requisito que `hola_agente/`).

## Decisiones de diseño

**¿Por qué no duplicar el ciclo ReAct?**
`app.py` importa `react_loop` directamente desde `hola_agente/agente_ddd.py`
agregando esa carpeta a `sys.path`. No hay paquete Python formal en el
laboratorio todavía — es la forma más simple de reusar código entre
prototipos sin reestructurar el repo.

**¿Dónde queda el log de "Ciclo N — RAZONANDO/ACTUANDO/OBSERVANDO"?**
Sigue imprimiéndose por `print()`, así que aparece en la terminal donde
corre `streamlit run`, no en el chat. El chat solo muestra la respuesta
final — para ver el ciclo ReAct paso a paso hay que mirar la consola.

## Aprendizajes clave

- La interfaz es una decisión separada del agente: el mismo `react_loop()`
  sirve para CLI y para chat sin tocar una línea de su lógica.
- `st.session_state` es la memoria de la sesión de Streamlit — sin eso,
  cada mensaje nuevo perdería el historial del chat.

## Próximo paso

Mostrar el ciclo ReAct (razonar/actuar/observar) también en la UI, no
solo en consola — por ejemplo con `st.status()` de Streamlit.
