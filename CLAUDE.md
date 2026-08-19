# CLAUDE.md — Laboratorio de Agentes basados en Claude

> *"No basta con aprender a programar agentes. Hay que aprender a pensar agénticamente."*
> — Víctor Valotto, 2026

---

## Propósito de este repositorio

Este repositorio es el laboratorio personal de **Víctor Valotto** para explorar, documentar y
construir sistemas agénticos basados en Claude (Anthropic). No es un proyecto de producción:
es un espacio de aprendizaje deliberado, prototipado acelerado e investigación aplicada.

El objetivo a largo plazo es desarrollar competencias sólidas en arquitectura de agentes para
aplicarlas en tres dominios principales:

- **Ingeniería de Software y DDD** — agentes que asistan en diseño de dominio, modelado y
  revisión de arquitectura.
- **Producción de contenido** — agentes que automaticen y aceleren la escritura de libros,
  reflexiones PMBOK, posts, ebooks modulares y guiones.
- **Docencia e investigación** — agentes para generar material didáctico, evaluar trabajos,
  gestionar contenido académico (FIUNER, posgrado IEC 62304).

---

## Contexto del autor

**Víctor Valotto** — Docente universitario (FIUNER, Facultad de Ingeniería), más de 30 años
en desarrollo de software. Materias: Ingeniería de Software, Gestión de Proyectos. Intereses
activos: DDD, IEC 62304, automatización con IA, escritura técnica y creativa, apnea.

**Stack tecnológico de este laboratorio:**
- Claude API + Claude Agent SDK (Anthropic)
- Python 3.x / Node.js
- Notion / Obsidian (gestión del conocimiento)
- Make / n8n (flujos de automatización, integración futura)

**Nivel de partida:** explorador inicial. Se parte de conceptos claros pero sin implementación
previa de agentes. El ritmo de aprendizaje es deliberado: comprensión profunda antes de
construcción.

---

## Estructura del repositorio

```
agentes-lab/
├── CLAUDE.md                  ← este archivo (contexto + hoja de ruta)
├── requirements.txt           ← dependencias del entorno (venv propio)
├── .env / .env.example        ← ANTHROPIC_API_KEY (afuera de git desde el día uno)
├── 00_fundamentos/            ← teoría, conceptos, investigación inicial
│   ├── notas/
│   │   ├── modelo_mental_agentico.md      ← entregable Etapa 1 (completo)
│   │   ├── diagramas_conceptos.md         ← diagramas del ciclo ReAct, agente, harness
│   │   └── manejo_memoria_agentica.md     ← notas sobre tipos de memoria (insumo Etapa 3)
│   └── referencias/           ← links, papers, docs de referencia
├── 01_prototipos/             ← experimentos y agentes mínimos funcionales
│   ├── hola_agente/           ← agente DDD, API directa, ciclo ReAct escrito a mano (completo)
│   ├── hola_agente_sdk/       ← mismo agente con Claude Agent SDK (completo)
│   └── hola_agente_web/       ← interfaz de chat en Streamlit sobre hola_agente (completo)
├── 02_proyectos/              ← proyectos más elaborados con objetivos claros
│   ├── asistente_ddd/         ← sin iniciar (Etapa 4)
│   ├── agente_contenido/      ← sin iniciar (Etapa 3)
│   └── agente_docente/        ← sin iniciar
├── 03_herramientas/           ← utilidades, wrappers, helpers reutilizables (vacío por ahora)
└── 04_reflexiones/            ← diario de aprendizaje, decisiones, lecciones (en curso)
```

**Convenciones:**
- Código en Python usa snake_case y type hints cuando es posible.
- Cada prototipo tiene su propio `README.md` con: objetivo, estado, aprendizajes clave.
- Los experimentos fallidos se documentan, no se eliminan. El error es datos.

---

## Hoja de ruta de aprendizaje

El plan está estructurado en cuatro etapas progresivas. Cada etapa tiene un entregable concreto
que actúa como validación del aprendizaje, no solo lectura.

**Estado actual (2026-08-06): Etapa 1 y Etapa 2 completas. Etapa 3 en curso.**

### Etapa 1 — Fundamentos del pensamiento agéntico (Semanas 1–3) — ✅ completa

El objetivo de esta etapa no es escribir código sino construir el modelo mental correcto.
Un agente no es un chatbot con más herramientas: es un sistema que razona, actúa y observa
en ciclos. Comprender esa diferencia es el primer aprendizaje real.

**Temas a investigar:**
- Qué es un agente de IA: definición, componentes, diferencias con LLM puro
- El ciclo ReAct: Razonamiento → Acción → Observación (Reason–Act–Observe)
- Tool use / function calling en la API de Claude
- Diferencia entre agente simple, agente con memoria y sistema multi-agente
- Qué es el Claude Agent SDK y cómo se relaciona con Cowork

**Entregable de la Etapa 1:**
Documento `00_fundamentos/notas/modelo_mental_agentico.md` con síntesis propia de los
conceptos anteriores, usando ejemplos del contexto personal (DDD, docencia o contenido).
**Estado: entregado.** Complementado con `diagramas_conceptos.md` (ciclo ReAct, estructura
del agente, tipos de harness, anatomía de `TOOLS_SCHEMA`) y un adelanto de investigación
sobre memoria (`manejo_memoria_agentica.md`) que ya sirve de insumo para la Etapa 3.

---

### Etapa 2 — Primer agente funcional (Semanas 4–6) — ✅ completa

La comprensión se consolida cuando se implementa. El primer agente debe ser mínimo pero real:
debe usar al menos una herramienta, mantener contexto entre turnos y producir un resultado útil.

**Temas a implementar:**
- Estructura básica de un agente con Claude API (Python)
- Definición y registro de herramientas (tool use)
- Manejo del ciclo de conversación (mensajes, roles, historial)
- Gestión de errores y respuestas inesperadas del modelo
- Logging básico para depuración y aprendizaje

**Proyecto piloto — `01_prototipos/hola_agente/`:**
Un agente que dado un concepto de DDD (Entidad, Agregado, Repositorio, etc.) genere:
1. Una definición en estilo Valotto (clara, con metáfora y ejemplo)
2. Una pregunta socrática para usar en clase
3. Un fragmento de código Python que ilustre el concepto

**Entregable de la Etapa 2:**
Prototipo funcional documentado + `README.md` con aprendizajes y decisiones de diseño.
**Estado: entregado, y ampliado a tres variantes** (no solo una):
- [`hola_agente/`](01_prototipos/hola_agente/) — API directa de Claude, ciclo ReAct (`while True`
  + parseo de `stop_reason`) escrito a mano, tools registradas con JSON Schema manual.
- [`hola_agente_sdk/`](01_prototipos/hola_agente_sdk/) — la misma tarea con el Claude Agent SDK
  (`query()`, decorador `@tool`, `create_sdk_mcp_server`), comparado línea a línea contra la
  versión de API directa en su README.
- [`hola_agente_web/`](01_prototipos/hola_agente_web/) — interfaz de chat en Streamlit que
  reutiliza `react_loop()` de `hola_agente/` sin duplicar lógica, para que el concepto DDD lo
  elija quien usa el agente y no el código.

Bug real encontrado y corregido durante esta etapa: `max_tokens=1024` cortaba respuestas largas
y el `stop_reason == "max_tokens"` caía en un `else` mudo — documentado en la entrada del
2026-08-06 del diario. Todavía sin manejo de errores de red/API en ninguno de los tres
prototipos (omisión consciente, aceptable para prototipos de aprendizaje).

---

### Etapa 3 — Agentes con memoria y estado (Semanas 7–10) — 🔶 en curso

Los agentes que cambian el mundo (o al menos un flujo de trabajo) necesitan recordar.
Esta etapa trabaja con persistencia, contexto largo y gestión del estado entre sesiones.

**Temas a explorar:**
- Tipos de memoria en sistemas agénticos: corto plazo (conversacional), largo plazo (vectorial),
  episódica (logs) y semántica (conocimiento del dominio)
- Integración con Notion/Obsidian como base de conocimiento externa
- Manejo de contexto largo en Claude (hasta 200k tokens)
- Patrones de diseño para agentes con estado: checkpointing, resumption

**Proyecto piloto — `02_proyectos/agente_contenido/`:**
Un agente que asista en la escritura del libro de DDD. Dado un capítulo planificado, el agente:
- Recupera notas previas relevantes (desde Obsidian/archivos locales)
- Genera un borrador con el estilo editorial Valotto
- Sugiere conexiones con capítulos anteriores
- Registra el avance en un log de escritura

**Entregable de la Etapa 3:**
Prototipo funcional + diagrama de arquitectura + reflexión sobre limitaciones encontradas.

**Punto de partida ya definido (no arrancar de cero):** los tres prototipos de Etapa 2 corren y
mueren sin dejar rastro entre sesiones — ninguno lee ni escribe nada fuera de su propio proceso.
El primer paso concreto de la Etapa 3 es convertir una de las tools (`generar_definicion()` en
`hola_agente/`, o su equivalente `GLOSARIO_DDD` en `hola_agente_sdk/`) para que lea notas reales
de Obsidian o de un archivo de dominio, en vez de generar todo desde cero o consultar un
diccionario hardcodeado en cada llamada. Ese paso es, a la vez, el cierre real de la Etapa 2 y la
puerta de entrada a la Etapa 3. Las notas de `manejo_memoria_agentica.md` ya cubren la base
teórica (tipos de memoria) necesaria para decidir el diseño.

---

### Etapa 4 — Sistemas multi-agente (Semanas 11–16)

El salto de un agente a un sistema de agentes es conceptualmente grande. Aquí aparecen
preguntas de orquestación, confianza entre agentes, coordinación y trazabilidad.

**Temas a explorar:**
- Patrones de orquestación: secuencial, paralelo, supervisado (orchestrator/worker)
- Comunicación entre agentes: paso de mensajes, estado compartido
- Subagentes especializados vs. agentes generalistas
- Trazabilidad y auditoría en sistemas multi-agente (relevante para IEC 62304)
- Manejo de errores y degradación graceful en el sistema

**Proyecto piloto — `02_proyectos/asistente_ddd/`:**
Sistema multi-agente para asistir en un taller de diseño de dominio:
- **Agente facilitador**: guía la sesión, hace preguntas, captura decisiones
- **Agente modelador**: convierte decisiones en estructuras DDD (Entidades, VOs, Agregados)
- **Agente documentador**: genera la documentación del dominio en formato exportable

**Entregable de la Etapa 4:**
Sistema funcional + análisis de arquitectura + lecciones para aplicar en IEC 62304.

---

## Proyectos experimentales planificados

Más allá de la hoja de ruta, estos son proyectos de aplicación real que esperan el nivel
de madurez adecuado para iniciarse:

| Proyecto | Dominio | Etapa mínima requerida | Estado |
|---|---|---|---|
| [Asistente IEC 62304 — Gestión de Cambios](02_proyectos/asistente_gestion_cambios/) | Calidad / Software médico | Etapa 3 | **POC funcional, adelantado a Etapa 4** |
| Generador de reflexiones PMBOK diarias | Contenido | Etapa 2 | Planificado |
| Evaluador automático de trabajos prácticos | Docencia | Etapa 3 | Planificado |
| GPT personalizado para trazabilidad IEC 62304 | Calidad | Etapa 4 | Planificado |
| Agente de diseño de dominio (DDD workshop) | Software | Etapa 4 | Planificado |

**Nota sobre el adelanto del Asistente IEC 62304:** este proyecto requería formalmente
cerrar la Etapa 3 antes de empezar (es, en la práctica, un sistema multi-agente —
territorio de Etapa 4). Se avanzó antes por interés puntual en un problema concreto:
convertir la skill `gestion-cambios-iec62304-8-2` (single-prompt sobre Jira) en un
backend con un agente por módulo, expuesto como API, con GitHub Issues (repo dedicado
`vvalotto/gestion-cambios-poc`) como almacén de estado y un frontend Streamlit de
prueba. El hallazgo central: convertir una skill en "agentes" no significa multiplicar
agentes por cada paso — significa identificar qué parte del diseño necesitaba dejar de
vivir en el prompt (acá, la autorización por rol, movida a la capa de API). Detalle
completo en el [README del proyecto](02_proyectos/asistente_gestion_cambios/README.md).
El salto de orden queda documentado, no oculto — la Etapa 3 sigue pendiente de cierre
por su propio mérito.

---

## Diario de aprendizaje

La carpeta `04_reflexiones/` contiene entradas con formato libre sobre:
- Decisiones de diseño tomadas y por qué
- Conceptos que costaron más de lo esperado
- Patrones que funcionaron y cuáles fallaron
- Preguntas abiertas para investigar

El diario no es documentación técnica: es el registro del pensamiento en evolución.
Escribirlo obliga a articular lo aprendido. Un concepto que no se puede explicar,
no está todavía comprendido.

---

## Principios de trabajo

**Comprensión antes de implementación.** No avanzar a la siguiente etapa sin poder explicar
la anterior con palabras propias y un ejemplo concreto.

**Prototipos pequeños y concretos.** Cada experimento debe ser ejecutable en menos de
30 minutos. Si un prototipo crece demasiado, es señal de que falta desglosar el problema.

**Los errores son datos.** Los experimentos que fallan se documentan con la misma atención
que los que funcionan. El error bien registrado es la mitad del aprendizaje.

**Conectar con el dominio real.** Cada prototipo debe tocar al menos uno de los tres dominios
de aplicación (DDD, contenido, docencia). El aprendizaje abstracto sin anclaje se olvida.

**Ritmo sostenible.** Este laboratorio no compite con nada. El objetivo es construir
competencia sólida, no velocidad. La antifragilidad se construye con exposición progresiva,
no con esfuerzo máximo sostenido.

---

## Recursos de referencia

### Documentación oficial
- [Claude API Docs](https://docs.anthropic.com)
- [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents)
- [Tool use / function calling](https://docs.anthropic.com/en/docs/tool-use)
- [Claude models overview](https://docs.anthropic.com/en/docs/models-overview)

### Lecturas recomendadas para Etapa 1
- "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022)
- "Cognitive Architectures for Language Agents" (Sumers et al., 2023)
- Documentación de Anthropic: "Building effective agents" — guía oficial de patrones agénticos

### Conexiones con proyectos existentes
- Libro DDD de Víctor Valotto — los agentes de esta ruta alimentarán ejemplos del libro
- Material PMBOK 365 reflexiones — el agente de contenido generará borradores para revisión
- Posgrado IEC 62304 — los patrones de trazabilidad multi-agente conectan directamente

---

*Creado: Abril 2026 | Autor: Víctor Valotto | Estado: activo, en evolución continua*
*Este archivo es un documento vivo. Se actualiza al completar cada etapa.*
*Migrado de `~/Documents/Claude/agentes` a `~/PycharmProjects/agentes-lab` el 2026-08-05 — proyecto ejecutable con venv propio, `requirements.txt` y control de versiones.*
*Actualizado el 2026-08-06 — Etapa 1 y Etapa 2 marcadas como completas, Etapa 3 en curso.*
