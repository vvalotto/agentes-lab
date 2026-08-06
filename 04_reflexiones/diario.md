# Diario de aprendizaje agéntico

> *"El diario no es documentación técnica: es el registro del pensamiento en evolución."*

Formato sugerido por entrada:

```
## [Fecha] — [Título libre]

**Lo que intenté:** ...
**Lo que aprendí:** ...
**Lo que no entendí todavía:** ...
**Próximo paso:** ...
```

---

## 2026-04-11 — Inicio del laboratorio

**Lo que intenté:** Configurar el repositorio, crear el CLAUDE.md y el primer documento
de investigación de la Etapa 1.

**Lo que aprendí:** Que la estructura del repositorio importa desde el primer día. Tener
carpetas claras (`00_fundamentos`, `01_prototipos`, etc.) reduce la fricción cuando hay
que decidir dónde poner cada cosa. El CLAUDE.md funciona como contexto persistente para
cualquier sesión de trabajo con Claude.

**Lo que no entendí todavía:** La diferencia práctica entre el Claude Agent SDK y usar
la API directamente. ¿Cuándo conviene uno sobre el otro?

**Próximo paso:** Leer el paper de ReAct y la guía "Building effective agents" de Anthropic.
Completar la sección 7 del modelo_mental_agentico.md con notas de esas lecturas.

---

## 2026-08-06 — El agente que a veces no terminaba

**Lo que intenté:** Tres cosas encadenadas, no una sola. Primero, sacar el laboratorio del disco
local: repo público en GitHub, rama `main`, `.env` afuera del control de versiones desde el día
uno. Después, una pregunta simple que resultó no serlo: ¿qué pasa si el concepto DDD no lo elijo
yo en el código, sino que lo pide quien está usando el agente? De ahí salió `hola_agente_web`, una
interfaz de chat en Streamlit que no reimplementa nada — llama directo a `react_loop()`, la misma
función que ya corría por consola en `hola_agente/agente_ddd.py`. Y en el medio de probarla, apareció
un tercer problema que no había pedido: el agente, a veces, simplemente no contestaba.

**Lo que aprendí:** Que separar el agente de su interfaz no es solo prolijidad — es lo que permite
detectar bugs que la interfaz original ocultaba. Corriendo por consola, "Value Object" y "Entidad"
se veían iguales: una salida de texto más o menos larga. En el chat, con espera visible y sesión que
no se reinicia sola, quedó expuesto que "Value Object" a veces terminaba en *"el agente no pudo
completar la tarea"*. La causa no era el modelo fallando: era `max_tokens=1024` cortando la respuesta
final justo cuando las tres tools (definición, pregunta socrática, código) devolvían más texto del
esperado, y el `stop_reason` volvía como `"max_tokens"` — un caso que el código ni siquiera nombraba,
solo caía en un `else` mudo. El bug estaba ahí desde el primer prototipo. Hizo falta cambiar el canal
de salida para que se hiciera visible. Con eso resuelto, la duda que arrastraba de la sesión anterior
—cuándo conviene el Agent SDK sobre la API directa— ya no es una duda: quedó documentada en el README
de `hola_agente_sdk`, con la comparación hecha y probada, no solo leída.

**Lo que no entendí todavía:** Si subir `max_tokens` es una solución robusta o un parche que
retrasa el mismo problema con conceptos DDD más largos que "Value Object". Y, más de fondo: nunca
hasta ahora escribí un `except` en ninguno de estos prototipos. Los tres agentes que tengo dan por
sentado que la API responde, que el modelo se comporta, que la red no falla. Eso no es un problema
todavía —son prototipos de aprendizaje, no producción—, pero es una omisión consciente que en algún
momento va a tener que dejar de serlo.

**Próximo paso:** Los tres prototipos de Etapa 2 (`hola_agente`, `hola_agente_sdk`, `hola_agente_web`)
siguen aislados: corren, responden, y mueren sin dejar rastro entre sesiones. Ninguno lee ni escribe
nada fuera de su propio proceso. Integrar — no solo crear — es lo que falta antes de dar la Etapa 2
por cerrada de verdad: que el agente lea notas reales de Obsidian o de un archivo de dominio en vez
de generar todo desde cero en cada llamada. Eso es, además, la puerta de entrada a la Etapa 3.

---
