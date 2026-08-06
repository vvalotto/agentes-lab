# hola_agente_sdk — Prototipo DDD con Claude Agent SDK

> Misma tarea que `hola_agente/`, reimplementada con el Claude Agent SDK
> en vez de la API directa. Compara los dos para ver qué provee el SDK
> que antes había que escribir a mano.

**Etapa:** 2 — Primer agente funcional
**Estado:** completo
**Tiempo estimado para ejecutarlo:** 5 minutos

---

## Qué hace este agente

Igual que `hola_agente/agente_ddd.py`: dado un concepto DDD, produce una
explicación con metáfora y un ejemplo de código Python. La diferencia no
está en el resultado — está en cómo se construye el agente.

---

## Cómo ejecutarlo

Requiere el Claude Code CLI instalado (el SDK lo invoca como subproceso):

```bash
claude --version   # debe responder con una versión, no un error
```

```bash
cd ../..   # raíz del proyecto (agentes-lab/)
source .venv/bin/activate
pip install -r requirements.txt   # instala claude-agent-sdk si falta

cd 01_prototipos/hola_agente_sdk
python agente_ddd_sdk.py
```

Este prototipo **no necesita `ANTHROPIC_API_KEY` en `.env`** — el SDK se
autentica a través de la sesión del Claude Code CLI ya logueada en esta
máquina. Si `claude --version` funciona, esto funciona.

---

## Diferencia clave frente a `hola_agente/`

| | `hola_agente/agente_ddd.py` (API directa) | `hola_agente_sdk/agente_ddd_sdk.py` (Agent SDK) |
|---|---|---|
| Loop ReAct | Escrito a mano (`while True` + parseo de `stop_reason`) | Provisto por `query()` — vos solo consumís mensajes |
| Cómo se definen las tools | Función Python + entrada manual en `TOOLS_SCHEMA` (JSON Schema a mano) | Decorador `@tool(nombre, descripción, {"arg": tipo})` |
| Cómo se conectan las tools | Dispatcher `TOOLS_IMPL` que vos mantenés | `create_sdk_mcp_server(...)` — un servidor MCP en memoria |
| Qué puede tocar el agente | Solo lo que vos ejecutás en `TOOLS_IMPL` | Lo que declares en `allowed_tools` — podés habilitar filesystem, bash, etc. del harness de Claude Code, o restringir a nada más que tus tools |
| Autenticación | `ANTHROPIC_API_KEY` en `.env` | Sesión del Claude Code CLI (o `ANTHROPIC_API_KEY` si se prefiere) |
| Costo real reportado | No — hay que calcularlo del `usage` de cada llamada | Sí — `ResultMessage.total_cost_usd` al final de la sesión |

---

## Arquitectura del código

```
agente_ddd_sdk.py
│
├── GLOSARIO_DDD        → datos locales (reemplaza las sub-llamadas a
│                          Claude que hacía hola_agente.py)
├── @tool                → declara la tool con su schema, todo en un decorador
├── create_sdk_mcp_server → empaqueta la tool en un servidor MCP en memoria
├── ClaudeAgentOptions    → system_prompt + allowed_tools + max_turns
└── query()               → el loop agéntico completo, como generador async
```

---

## Decisiones de diseño

**¿Por qué la tool consulta un diccionario en memoria y no llama a Claude?**
Para mostrar el otro patrón válido de tool: en `hola_agente.py` las tools
hacían sub-llamadas al modelo; acá la tool es una consulta de datos local
(como leería un archivo o una base de datos). Los dos patrones conviven en
sistemas reales — el punto es que la tool puede ser cualquier función
Python, no importa qué hace adentro.

**¿Por qué restringir `allowed_tools` a solo la tool del glosario?**
Por defecto, el Agent SDK expone (según configuración) el harness completo
de Claude Code: lectura/escritura de archivos, bash, etc. Para este
prototipo educativo, restringir a una sola tool hace explícito que el
alcance del agente es una decisión de configuración, no un default que
hay que aceptar.

**¿Por qué `anyio.run()` y no `asyncio.run()`?**
El SDK es async-first y el ejemplo oficial usa `anyio` como runner
agnóstico. Con `asyncio.run()` también funcionaría para este caso simple.

---

## Aprendizajes clave

- El SDK no reemplaza el ciclo ReAct — lo empaqueta. `query()` sigue
  siendo razonar → actuar → observar por debajo; solo que ya no lo
  escribís vos.
- Una tool en el Agent SDK es una función async que devuelve
  `{"content": [{"type": "text", "text": ...}]}` — mismo shape de
  `tool_result` que en la API directa, pero declarada con menos código.
- `allowed_tools` es el control de superficie del agente: sin declarar
  explícitamente una tool ahí, el agente no puede usarla aunque esté
  definida y conectada.
- El costo real de la sesión llega en `ResultMessage.total_cost_usd` —
  no hay que calcularlo a mano sumando tokens por llamada.

---

## Próximo paso (Etapa 3)

Cambiar `GLOSARIO_DDD` por una tool que lea notas reales de Obsidian o de
`docs/dominio/` de otro proyecto, incorporando memoria de largo plazo real
en vez de un diccionario hardcodeado.
