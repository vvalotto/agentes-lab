# Modelo mental agéntico — Etapa 1

> *Este documento es un punto de partida, no una definición canónica.*
> *Su propósito es construir el modelo mental correcto antes de escribir una sola línea de código.*
> *Cada sección debe ser confrontada con las fuentes de referencia y reescrita con palabras propias.*

Estado: **en construcción** | Inicio: Abril 2026

---

## 1. La pregunta que lo organiza todo

Antes de definir qué es un agente, conviene detenerse en la pregunta que justifica aprenderlo:

**¿Por qué un LLM solo no alcanza?**

Un modelo de lenguaje (Claude, GPT, etc.) es extraordinariamente capaz de razonar sobre un
problema cuando toda la información necesaria está en el prompt. Pero el mundo real impone
restricciones que un LLM puro no puede superar:

- La información que necesita no está en el contexto: está en un archivo, una API, una base de datos.
- La tarea requiere más de un paso, y el resultado de cada paso cambia lo que hay que hacer después.
- El entorno cambia mientras el modelo trabaja: una búsqueda puede devolver resultados distintos
  en cada invocación.
- Algunas acciones tienen efectos reales (escribir un archivo, enviar un mensaje, llamar una API)
  que no son reversibles.

Un agente es la respuesta arquitectónica a esas restricciones. No es un LLM "mejorado": es un
sistema que usa un LLM como motor de razonamiento, pero lo rodea de herramientas, memoria y
ciclos de retroalimentación.

---

## 2. Qué es un agente de IA

Una definición operativa útil:

> **Un agente de IA es un sistema que percibe su entorno, razona sobre él, decide qué acción
> ejecutar y actúa — repitiendo este ciclo hasta alcanzar un objetivo.**

Los componentes esenciales son cuatro:

**Modelo de lenguaje (el motor de razonamiento)**
Es quien decide. Analiza el estado actual, interpreta el resultado de la última acción y
determina qué hacer a continuación. En el contexto de este laboratorio, este motor es Claude.

**Herramientas (tools)**
Son las acciones que el agente puede ejecutar en el mundo. Una herramienta puede ser: buscar
en la web, leer un archivo, llamar una API, ejecutar código, consultar una base de datos.
Sin herramientas, el agente solo puede producir texto. Con herramientas, puede actuar.

**Memoria**
Es la información que el agente conserva entre pasos. Puede ser de corto plazo (el historial
de la conversación actual), largo plazo (una base de conocimiento persistente) o episódica
(logs de acciones pasadas). Sin memoria, cada paso comienza desde cero.

**Ciclo de ejecución**
Es la estructura que conecta los tres componentes anteriores. El agente no ejecuta todo de
una vez: razona, actúa, observa el resultado, razona de nuevo. Este ciclo se repite hasta
que el objetivo se alcanza (o se detecta que no puede alcanzarse).

---

## 3. El ciclo ReAct

ReAct (Reason + Act) es el patrón fundamental que estructura la mayoría de los agentes modernos.
Fue formalizado por Yao et al. (2022) y es el modelo mental más útil para empezar.

El ciclo tiene tres fases que se repiten:

```
┌─────────────────────────────────────────────────────────────┐
│                        CICLO ReAct                          │
│                                                             │
│   [Observación]                                             │
│        │                                                    │
│        ▼                                                    │
│   [Razonamiento]  ←── "¿Qué sé? ¿Qué me falta? ¿Qué hago?"│
│        │                                                    │
│        ▼                                                    │
│   [Acción]        ←── Llama a una herramienta              │
│        │                                                    │
│        ▼                                                    │
│   [Observación]   ←── Resultado de la herramienta          │
│        │                                                    │
│        └──────────────────────────────────────────── (loop)│
└─────────────────────────────────────────────────────────────┘
```

**Razonamiento:** El modelo analiza el estado actual. ¿Qué información tiene? ¿Qué le falta?
¿Cuál es el siguiente paso lógico? Este paso suele producirse como texto interno ("pensamiento")
antes de decidir una acción. En Claude, esto puede ser explícito (thinking) o implícito.

**Acción:** El modelo invoca una herramienta con parámetros específicos. La acción puede ser
`buscar("DDD Aggregate pattern")`, `leer_archivo("capitulo_3.md")` o `generar_codigo(concepto)`.

**Observación:** El resultado de la herramienta vuelve al modelo como nueva información. Esta
observación alimenta el siguiente ciclo de razonamiento. El modelo actualiza su comprensión
del estado del mundo.

### Ejemplo concreto (dominio DDD)

Objetivo: *"Explicá el concepto de Agregado en DDD con un ejemplo de código Python."*

- **Razonamiento 1:** Tengo el concepto pedido. Necesito definición, metáfora y código.
  Primero busco documentación actualizada sobre Aggregates en DDD.
- **Acción 1:** `buscar("DDD Aggregate Evans definition site:martinfowler.com")`
- **Observación 1:** Resultado con definición de Evans + artículo de Fowler.
- **Razonamiento 2:** Tengo la definición. Ahora necesito construir un ejemplo Python
  relevante para el contexto de FIUNER. Voy a generar el código.
- **Acción 2:** `generar_codigo(concepto="Aggregate", dominio="sistema_universitario")`
- **Observación 2:** Código generado.
- **Razonamiento 3:** Tengo definición y código. Puedo construir la respuesta final
  con metáfora y pregunta socrática.
- **Acción 3:** `responder(formato="estilo_valotto")`

---

## 4. Tool use / function calling en Claude

El mecanismo que permite a Claude interactuar con herramientas se llama *tool use* (o
*function calling*). Es el puente entre el razonamiento del modelo y las acciones en el mundo.

### Cómo funciona

1. Se define una herramienta con: nombre, descripción, y esquema de parámetros (JSON Schema).
2. Se incluye la definición en la llamada a la API de Claude.
3. Claude decide cuándo invocar la herramienta y con qué parámetros.
4. La herramienta se ejecuta del lado del cliente (en tu código Python).
5. El resultado se devuelve a Claude como nuevo contexto.
6. Claude continúa razonando con ese resultado.

### Estructura mínima en Python

```python
import anthropic

client = anthropic.Anthropic()

# Definición de la herramienta
tools = [
    {
        "name": "buscar_documentacion",
        "description": "Busca documentación técnica sobre un concepto de DDD.",
        "input_schema": {
            "type": "object",
            "properties": {
                "concepto": {
                    "type": "string",
                    "description": "El concepto DDD a buscar (ej: 'Aggregate', 'Value Object')"
                }
            },
            "required": ["concepto"]
        }
    }
]

# Llamada con herramienta disponible
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "Explicame qué es un Aggregate en DDD"}
    ]
)

# Si Claude decide usar la herramienta, stop_reason será "tool_use"
if response.stop_reason == "tool_use":
    tool_call = response.content[0]
    print(f"Herramienta: {tool_call.name}")
    print(f"Parámetros: {tool_call.input}")
    # Aquí ejecutás la herramienta real y devolvés el resultado a Claude
```

**Lo importante:** Claude no ejecuta la herramienta. Claude *decide* invocarla y especifica
los parámetros. Tu código Python ejecuta la función real y devuelve el resultado. Esta
separación es fundamental para entender el control de flujo en sistemas agénticos.

---

## 5. Tipos de agentes: de simple a multi-agente

No todos los sistemas agénticos son iguales. Hay una progresión natural de complejidad:

### Agente simple (single-agent loop)
Un único modelo en un ciclo ReAct. Tiene acceso a un conjunto de herramientas y gestiona
todo el razonamiento. Es el punto de partida correcto. La mayoría de los casos de uso
reales se pueden resolver con un agente bien diseñado.

*Cuándo es suficiente:* tareas que pueden descomponerse secuencialmente, con un dominio
de conocimiento relativamente acotado y herramientas bien definidas.

### Agente con memoria persistente
Un agente simple que además puede leer y escribir en una base de conocimiento externa
(archivos, Notion, base vectorial). La memoria permite que el agente aprenda entre sesiones
y mantenga contexto a largo plazo.

*Cuándo es necesario:* tareas que se ejecutan en múltiples sesiones (como asistir en la
escritura de un libro), o que requieren acceder a conocimiento previo acumulado.

### Sistema multi-agente
Múltiples modelos que colaboran: un orquestador que divide el problema y delega en
subagentes especializados. Cada subagente tiene su propio conjunto de herramientas y
contexto.

*Cuándo es necesario:* tareas que pueden paralelizarse, que requieren expertise muy
diferente en cada parte, o que exceden el contexto de un único modelo.

*Advertencia:* la complejidad de un sistema multi-agente es significativamente mayor.
La comunicación entre agentes, la trazabilidad de decisiones y el manejo de errores
se multiplican. No agregar esta capa hasta que un agente simple haya demostrado sus
límites.

---

## 6. Claude Agent SDK y su relación con Cowork

El **Claude Agent SDK** es el framework oficial de Anthropic para construir sistemas agénticos.
Provee abstracciones sobre la API de Claude que facilitan:

- La gestión del ciclo agéntico (loop ReAct automatizado)
- La definición y registro de herramientas
- La coordinación entre agentes (orquestación)
- El manejo de contexto y memoria

**Cowork** es la implementación de este SDK en el entorno de escritorio de Anthropic. Cuando
trabajás en Cowork, estás interactuando con un agente construido sobre el Claude Agent SDK,
con acceso a herramientas de sistema de archivos, shell, y MCPs (Model Context Protocol).

**MCP (Model Context Protocol)** es el estándar abierto de Anthropic para conectar agentes
con fuentes de datos y herramientas externas. Permite que el agente acceda a Notion, GitHub,
Google Drive, bases de datos y otras integraciones sin código personalizado para cada una.

Para este laboratorio, el stack de trabajo es:
- Claude API directa (Python) para prototipos y aprendizaje profundo
- Claude Agent SDK para proyectos más elaborados
- MCPs para integrar fuentes externas (Obsidian, Notion, GitHub)

---

## 7. Preguntas abiertas (a responder con investigación y práctica)

Estas preguntas no tienen respuesta todavía. Son el horizonte de la Etapa 1:

1. ¿Cómo determina Claude *cuándo* usar una herramienta vs. responder directamente?
   ¿Esto es controlable desde el prompt o es una decisión del modelo?

2. ¿Cuál es el límite práctico del ciclo ReAct? ¿Cuántos pasos puede dar un agente
   antes de perder coherencia o acumular errores?

3. ¿Cómo se gestiona el contexto cuando la conversación se hace muy larga? ¿El agente
   empieza a "olvidar" pasos anteriores?

4. ¿Qué pasa cuando una herramienta falla? ¿Claude puede recuperarse solo o necesita
   lógica explícita de manejo de errores en el código?

5. ¿Cómo se diferencia un agente con acceso a Obsidian (vía MCP) de uno que lee
   archivos directamente? ¿Cuándo conviene cada enfoque?

---

## 8. Entregable de la Etapa 1

**Documento a completar:** este mismo archivo, enriquecido con:
- Síntesis propia de las lecturas recomendadas (ReAct paper, Cognitive Architectures, guía Anthropic)
- Ejemplos propios del contexto DDD/docencia/contenido para cada concepto
- Respuestas (parciales o definitivas) a las preguntas abiertas de la sección 7
- Al menos una metáfora original que explique el ciclo agéntico

**Criterio de completitud:** poder explicar oralmente, sin notas, la diferencia entre
un LLM puro y un agente, el ciclo ReAct y los cuatro tipos de memoria agéntica — usando
ejemplos del dominio propio.

---

## Referencias para esta etapa

- Yao et al. (2022). *ReAct: Synergizing Reasoning and Acting in Language Models.* [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
- Sumers et al. (2023). *Cognitive Architectures for Language Agents.* [arXiv:2309.02427](https://arxiv.org/abs/2309.02427)
- Anthropic. *Building effective agents.* [docs.anthropic.com/en/docs/agents](https://docs.anthropic.com/en/docs/agents)
- Anthropic. *Tool use overview.* [docs.anthropic.com/en/docs/tool-use](https://docs.anthropic.com/en/docs/tool-use)
- Anthropic. *Model Context Protocol.* [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

*Última actualización: Abril 2026 | Etapa: 1 de 4 | Estado: borrador inicial*
