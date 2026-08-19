# asistente_gestion_cambios — Backend multi-agente para IEC 62304 8.2

> Rediseño agéntico de la skill `gestion-cambios-iec62304-8-2` (single-prompt,
> sobre Jira): un agente por módulo, expuestos como API, con GitHub Issues
> (repo dedicado) como almacén de estado y evidencia. Frontend Streamlit como
> cliente de prueba.

**Etapa:** 4 — Sistemas multi-agente, **adelantada**. El roadmap del
laboratorio marca este proyecto como dependiente de cerrar la Etapa 3
primero; se decidió avanzar antes por interés puntual en el problema de
autorización, no por arrastre del orden. Queda documentado acá para que
quede explícito, no oculto.

**Estado:** POC funcional — Módulos 1 (Solicitud) y 2 (Aprobación) de los 5
de la norma. Módulos 3 (Implementación), 4 (Verificación) y 5 (Trazabilidad)
sin implementar — ver "Próximo paso".

**Tiempo estimado para ejecutarlo:** 10 minutos (requiere repo GitHub propio
y una API key de Anthropic).

---

## Por qué existe este proyecto

Se analizó la skill `gestion-cambios-iec62304-8-2` como candidata a
rediseño agéntico. La conclusión: partir sus 5 módulos en subagentes por
simetría no agrega valor por sí solo — el módulo ya resolvía el "routing"
entre etapas barato, dentro de un solo prompt. Lo que sí agrega valor real
es sacar la **autorización por rol** de "preguntarle al modelo y confiar en
la respuesta" (así estaba en la skill original) y llevarla a un **límite de
sistema real** — y eso solo tiene sentido si el flujo deja de vivir en una
conversación de Claude Code y pasa a ser un backend de API que un frontend
consume.

Este POC prueba exactamente ese punto, con el alcance mínimo necesario para
ejercitarlo: los 2 módulos donde el gate de autorización importa
(Solicitud, que cualquier rol autorizado puede iniciar; Aprobación, donde
la clase IEC 62304 del cambio determina quién puede decidir).

## Qué demuestra el POC

- Un **agente por módulo** (`backend/agents/agente_solicitud.py`,
  `agente_aprobacion.py`): cada uno es una llamada a la API de Claude con
  un system prompt especializado que redacta la description/comentario del
  Issue a partir de datos crudos — no un loop ReAct con tools propias (ver
  "Decisiones de diseño" abajo, por qué).
- Un **backend de API** (FastAPI) que expone esos agentes: `POST
  /solicitudes` y `POST /solicitudes/{clave}/aprobacion`.
- **GitHub Issues** (repo dedicado, no `agentes-lab`) como almacén de
  estado — los 7 estados del workflow original se modelan como labels
  `estado:*`, validados por una máquina de estados propia
  (`backend/core/state_machine.py`), porque GitHub no ofrece un workflow
  configurable como el de Jira.
- **Autorización por rol en la capa de API** (`backend/core/auth.py`): cada
  request lleva un header `X-Api-Key`, resuelto a un rol contra un mapeo
  del `.env`. Si el rol no autoriza la acción, el endpoint devuelve 403
  **antes** de tocar el agente o GitHub — probado en vivo con la UI (ver
  captura del flujo en la sesión de implementación): un rol sin permiso de
  aprobar Clase A recibe el 403 con el mensaje explícito de por qué.
- Un **frontend Streamlit** (`frontend/app.py`) que consume la API como
  cualquier cliente externo lo haría — no tiene acceso directo a Claude ni
  a GitHub.

## Cómo ejecutarlo

```bash
cd /Users/victor/PycharmProjects/agentes-lab
source .venv/bin/activate
pip install -r requirements.txt -r 02_proyectos/asistente_gestion_cambios/requirements.txt

cd 02_proyectos/asistente_gestion_cambios
cp .env.example .env   # completar GITHUB_TOKEN (gh auth token), GITHUB_REPO, ANTHROPIC_API_KEY, ROLES_API_KEYS

uvicorn backend.main:app --port 8731            # terminal 1
API_BASE_URL=http://127.0.0.1:8731 streamlit run frontend/app.py --server.port 8502   # terminal 2
```

El repo dedicado de este POC es
[`vvalotto/gestion-cambios-poc`](https://github.com/vvalotto/gestion-cambios-poc)
(privado), con los labels `estado:*` y `clase-*` ya creados.

## Decisiones de diseño

**¿Por qué GitHub Issues y no Jira, si la skill original ya resolvía esto
con Jira?** Interés puntual en el patrón "repo de producto propio", más
cercano al contexto del laboratorio. El costo real: GitHub no tiene
workflow configurable, así que la validación de transiciones que en Jira
venía gratis de la herramienta acá la implementa
`backend/core/state_machine.py` a mano — ningún endpoint aplica un cambio
de label `estado:*` sin haber validado primero que la transición es legal
desde el estado actual.

**¿Por qué cada agente es una sola llamada a Claude y no un loop con
tools?** Las acciones que necesitan una tool (crear el Issue, comentar,
aplicar labels, transicionar) son determinísticas — no requieren que un
modelo decida "qué tool llamar", las ejecuta el backend directo contra la
API de GitHub. El agente aporta lo único que sí requiere juicio: redactar
la description/comentario en la estructura de la plantilla a partir de
datos crudos. Meter un ReAct loop ahí (Agent SDK, subprocess) habría sido
complejidad sin contrapartida.

**¿Por qué la autorización se resuelve por API key y no por rol declarado
en el body?** Porque ese es exactamente el punto que motivó todo el
rediseño: en la skill original, el "rol" lo decía el usuario en el chat, y
el modelo confiaba en la respuesta. Acá el rol lo determina qué credencial
usó quien llama — el body nunca puede mentir sobre quién es el aprobador.

## Aprendizajes clave

- Convertir una skill en "agentes" no significa multiplicar agentes por
  cada paso del proceso — significa identificar qué parte del diseño
  necesitaba dejar de vivir en el prompt. Acá era un punto solo (la
  autorización), no los cinco módulos.
- Cambiar la herramienta de tracking (Jira → GitHub) no es neutro: se
  llevó una validación gratis (el workflow) a código propio. Vale la pena
  nombrarlo como costo explícito de la decisión, no descubrirlo tarde.
- Un "agente" no necesita ser un loop ReAct para ser un agente útil en un
  sistema mayor — acá cada uno es una function call especializada, y el
  backend orquesta determinísticamente alrededor.

## Próximo paso

Extender el mismo patrón (agente de redacción + router con
autorización/transición validadas antes de tocar GitHub) a los tres
módulos que quedaron fuera de este POC:

- **Módulo 3 — Implementación** (8.2.2): comentario con lo modificado,
  idealmente enlazado a un commit/PR real del repo de producto.
- **Módulo 4 — Verificación** (8.2.3): comentario con evidencia de
  pruebas; idealmente quien verifica no es quien implementó (otro punto
  donde el gate de rol importa).
- **Módulo 5 — Trazabilidad** (8.2.4): no corresponde a un Issue
  individual sino a una consulta agregada (`searchJiraIssuesUsingJql` →
  búsqueda de Issues por label/estado en GitHub) que arma una matriz de
  cumplimiento.

`backend/agents/` y `backend/routers/` ya están preparados para recibirlos
sin reestructurar nada.
