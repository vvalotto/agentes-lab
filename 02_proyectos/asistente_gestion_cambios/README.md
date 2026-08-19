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

**Estado:** POC funcional — Módulo 1 (Solicitud) con **tres canales de
entrada** (formulario, chat, mail vía IMAP) y Módulo 2 (Aprobación), de los 5
de la norma. Módulos 3 (Implementación), 4 (Verificación) y 5 (Trazabilidad)
sin implementar — ver "Próximo paso".

**Tiempo estimado para ejecutarlo:** 10 minutos (requiere repo GitHub propio
y una API key de Anthropic; el canal mail es opcional y necesita además una
cuenta de Gmail con contraseña de aplicación).

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
- Un **canal chat** para el Módulo 1 (`POST /chat/mensaje`,
  `backend/agents/agente_extraccion.py`): en vez de llenar el formulario,
  el usuario cuenta el problema en lenguaje libre y un segundo agente
  completa `SolicitudIn` de a poco, preguntando puntualmente lo que falta,
  hasta poder crear el Issue con el mismo `casos_de_uso.crear_solicitud()`
  que usa el formulario. Ver "Agente de extracción" abajo.
- Un **canal mail** (`GET /mail/recientes`, `GET /mail/{uid}`,
  `backend/core/mail_reader.py`): lee por IMAP una etiqueta dedicada de
  Gmail (no INBOX completo) y manda el contenido del correo elegido como
  primer mensaje al mismo `POST /chat/mensaje` del canal chat — cero
  lógica de negocio nueva, solo un adaptador de lectura. El disparo sigue
  siendo humano (el usuario elige "usar este mail"), no un listener
  automático — ver "Canal mail" abajo, por qué.

## Agente de extracción — canal chat

Pensado para acercar el Módulo 1 a un usuario que "no tiene tiempo para
explicar demasiado": en vez de un formulario estructurado, escribe en
lenguaje libre y el sistema arma los datos.

- **Es el inverso de `agente_solicitud`**: ese recibe datos limpios y
  redacta prosa; `agente_extraccion` recibe prosa suelta y devuelve datos
  limpios. Una vez extraídos, el pipeline es idéntico al del formulario —
  no se duplicó ninguna lógica de negocio (ver refactor a
  `core/casos_de_uso.py` en "Decisiones de diseño").
- **Tool-use forzado, no JSON en texto libre**: `extraer_campos()` declara
  una tool cuyo `input_schema` espeja los 8 campos de `SolicitudIn` y
  fuerza al modelo a llamarla (`tool_choice`), pasándole *todo* el
  historial de la conversación en cada turno — así el modelo hace el merge
  entre turnos y el backend no necesita lógica propia de fusión.
- **Qué falta se detecta reusando la validación que ya existe**: se
  intenta construir `SolicitudIn(**campos)`; si `pydantic.ValidationError`,
  los campos en el error son exactamente los que faltan — sin mantener una
  lista de "requeridos" por separado.
- **Sigue sin ser un loop ReAct abierto**: son dos llamadas acotadas por
  turno (extraer con tool forzada; si falta algo, una segunda llamada de
  texto simple —`agente_extraccion.preguntar_por_faltantes()`, reusando
  `agents/_cliente.py::redactar()` tal cual— para la pregunta de
  seguimiento). Mismo principio que el resto del backend: el código
  orquesta, el modelo aporta juicio en pasos angostos.
- **Probado con texto realista y desprolijo** (mensajes largos, hasta con
  información repetida/mezclada) y extrajo datos limpios y coherentes en
  2-3 turnos — ver Issues de prueba cerrados en el repo dedicado.

## Canal mail — IMAP disparado por humano

Motivado por acercar todavía más el Módulo 1 al usuario final: alguien le
manda un mail a la cuenta de un humano del equipo, y es **ese humano quien
decide** hacer que el agente lo lea — no el buzón procesando solo lo que
llega.

- **Por qué "disparado por humano" y no un listener automático**: si el
  buzón procesara mails entrantes sin que nadie los mire, reaparece el
  problema de autorización que motivó todo este rediseño (¿cómo confío en
  quién manda el mail, sin que nadie lo confirme?). Con un humano
  autenticado eligiendo qué mail usar, la identidad sigue siendo la sesión
  (`X-Api-Key` → rol) — el remitente real del mail es un dato más que
  extrae `agente_extraccion` (`solicitante`, `origen_reporte`), nunca una
  credencial.
- **Cero lógica de negocio nueva**: `backend/core/mail_reader.py` solo
  lista y lee correos por IMAP (`imaplib`/`email` de la librería estándar,
  sin dependencias nuevas). El texto que produce se manda tal cual a
  `POST /chat/mensaje` — el mismo pipeline de extracción, validación y
  creación del Issue que ya existía para el chat manual, sin tocarlo.
- **Contraseña de aplicación de Gmail, no OAuth**: mismo patrón que
  `GITHUB_TOKEN`/`ANTHROPIC_API_KEY` — un secreto en `.env`, sin registrar
  una app OAuth. Requiere verificación en 2 pasos activada en la cuenta y
  generarla en myaccount.google.com/apppasswords (ver `.env.example`).
- **Etiqueta dedicada, no INBOX completo**: el adaptador solo lee la
  etiqueta configurada en `IMAP_ETIQUETA` (default `gestion-cambios`) —
  probado explícitamente que un mail fuera de esa etiqueta no aparece en
  `/mail/recientes`, aunque el INBOX real tenga miles de mensajes.
- **Canal opcional**: si `IMAP_USER`/`IMAP_APP_PASSWORD` no están en el
  `.env`, el resto del backend (formulario, chat, aprobación) arranca
  igual — `mail_reader.py` recién falla, con un mensaje claro, cuando
  alguien intenta usar ese canal puntual.

## Cómo ejecutarlo

```bash
cd /Users/victor/PycharmProjects/agentes-lab
source .venv/bin/activate
pip install -r requirements.txt -r 02_proyectos/asistente_gestion_cambios/requirements.txt

cd 02_proyectos/asistente_gestion_cambios
cp .env.example .env   # completar GITHUB_TOKEN (gh auth token), GITHUB_REPO, ANTHROPIC_API_KEY, ROLES_API_KEYS
# IMAP_* es opcional — solo hace falta si vas a probar el canal mail

uvicorn backend.main:app --port 8731            # terminal 1
API_BASE_URL=http://127.0.0.1:8731 streamlit run frontend/app.py --server.port 8502   # terminal 2
```

El repo dedicado de este POC es
[`vvalotto/gestion-cambios-poc`](https://github.com/vvalotto/gestion-cambios-poc)
(privado), con los labels `estado:*` y `clase-*` ya creados.

## Deploy — Fly.io

Desplegado en **https://gestion-cambios-poc.fly.dev/** — una sola app de
Fly, dos grupos de proceso (`backend`, `frontend`), definidos en
`fly.toml`. El canal mail queda **afuera de este deploy** a propósito
(no se cargaron `IMAP_USER`/`IMAP_APP_PASSWORD` como secrets) — exponer la
contraseña de aplicación de Gmail en un host público es una decisión
aparte, todavía no tomada.

```bash
cd 02_proyectos/asistente_gestion_cambios
fly apps create gestion-cambios-poc          # una vez
fly secrets set GITHUB_TOKEN=... GITHUB_REPO=... ANTHROPIC_API_KEY=... ROLES_API_KEYS=...
fly deploy
```

**Decisiones de la infraestructura, con su motivo:**

- **`requirements.txt` del proyecto quedó autocontenido** (duplica
  `anthropic`/`streamlit`, antes solo vivían en el `requirements.txt` raíz
  del laboratorio) — el build de Docker solo tiene como contexto esta
  carpeta, no el monorepo completo.
- **El backend no tiene `[[services]]` público en `fly.toml`.** El primer
  intento exponía backend y frontend en el puerto 443 de la misma app, y
  el ruteo quedaba ambiguo (a veces `/health` devolvía el HTML de
  Streamlit). El backend solo necesita ser alcanzable *entre* las dos
  Machines de la app — el frontend lo encuentra por la red privada de Fly
  (`backend.process.gestion-cambios-poc.internal:8731`, seteado como
  `API_BASE_URL` en `[env]`).
- **`uvicorn` bindea a `--host ::` (IPv6), no `0.0.0.0`.** La red privada
  de Fly (6PN) es IPv6 — un backend bindeado solo a IPv4 responde bien a
  tráfico público pero rechaza las conexiones internas entre Machines
  (`Connection refused`, no timeout). Fue el bug real que hubo que
  diagnosticar por SSH (`fly ssh console`) antes de que el chat funcionara
  contra la URL pública.

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
  backend orquesta determinísticamente alrededor. El canal chat sumó un
  segundo agente (extracción) sin romper ese principio: sigue siendo dos
  llamadas acotadas por turno, no un loop abierto.
- Extraer la lógica de negocio del router (`core/casos_de_uso.py`) *antes*
  de necesitar un segundo canal hizo que agregar el chat fuera casi solo
  el agente nuevo — el refactor pagó de inmediato, no fue trabajo
  especulativo.
- El canal mail terminó siendo casi gratis por la misma razón: como el
  chat ya aceptaba cualquier texto libre como primer mensaje, "leer un
  mail" resultó ser solo "producir texto y mandarlo al mismo lugar" — cero
  código de negocio nuevo, solo un adaptador de lectura (IMAP).
- El disparador humano (elegir qué mail usar) resolvió el problema de
  identidad del canal sin inventar nada: la sesión autenticada sigue
  siendo la fuente de verdad del rol, el mail es solo datos. La alternativa
  (un listener automático sobre el buzón) habría reabierto exactamente el
  problema de autorización que motivó todo este proyecto.

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
