# Manejo y tipos de memoria agéntica — Etapa 3

> *Este documento es un punto de partida, no una definición canónica.*
> *Su propósito es construir el modelo mental correcto antes de tocar código de `agente_contenido`.*
> *Cada sección debe confrontarse con la práctica y reescribirse si la práctica la contradice.*

Estado: **en construcción** | Inicio: Agosto 2026

---

## 1. Por qué la API es stateless y qué implica

La Claude API no recuerda nada entre llamadas. No hay una sesión abierta del lado del
servidor que vaya acumulando contexto sola: cada vez que se llama a
`client.messages.create()`, el modelo solo sabe lo que está explícitamente en el
parámetro `messages` de esa llamada puntual. Si no se lo mandás, no existe para él.

Esto no es una limitación menor que "algún día se arregla" — es la base sobre la que se
construye todo lo demás en este documento. **Memoria, en la práctica, siempre es una de
estas dos cosas:**

1. **Meter más cosas en el contexto de la próxima llamada** (reenviar el historial,
   inyectar un resultado de búsqueda antes de preguntar)
2. **Guardar algo afuera del proceso**, para que un proceso *futuro* — otra llamada,
   otra sesión, otro día — lo lea y lo vuelva a meter en el contexto de ese momento

Ya viví esta distinción sin nombrarla en los prototipos de Etapa 2. En
`hola_agente_web/app.py`, `st.session_state.mensajes` es memoria del primer tipo: vive
mientras el proceso de Streamlit está corriendo, y desaparece apenas cierro la pestaña
o reinicio el servidor. No hay nada en ninguno de mis tres prototipos que sobreviva el
proceso — cada consulta al `GLOSARIO_DDD` de `hola_agente_sdk` es una lectura de un
diccionario en RAM, no de algo persistido en disco. Etapa 3 es, en el fondo, la etapa
donde eso deja de ser cierto.

---

## 2. Los cuatro tipos de memoria

No es una sola cosa disfrazada de cuatro nombres — son cuatro mecanismos distintos que
resuelven preguntas distintas, con implementaciones y costos distintos.

### Memoria de corto plazo (conversacional)

Resuelve: *"¿qué dijimos hace dos mensajes?"*. Vive en el array `messages` que se
reenvía completo en cada llamada — no hay otro lugar donde viva. Es la memoria más
barata de implementar (no hace falta ninguna infraestructura extra) y la más cara de
escalar (cada mensaje del historial se paga en tokens en cada llamada siguiente).

*Ejemplo propio:* el historial dentro de `react_loop()` en `hola_agente/agente_ddd.py`
— la lista `messages` que crece con cada ciclo del loop ReAct, y que se descarta apenas
la función retorna.

### Memoria de largo plazo (vectorial)

Resuelve: *"¿qué sé sobre esto de sesiones anteriores?"*. Vive en una base de datos
externa al proceso — típicamente una base vectorial que permite buscar por similitud
semántica, no por coincidencia exacta de texto. Esta es la memoria que le falta a
`agente_contenido`: para sugerir conexiones con capítulos anteriores del libro de DDD,
el agente necesita poder buscar en todo lo que ya se escribió, no solo en lo que está
en el prompt actual.

*Ejemplo propio:* el prototipo piloto de Etapa 3 planificado en el roadmap — un agente
que "recupera notas previas relevantes desde Obsidian/archivos locales" antes de
generar un borrador.

### Memoria episódica (logs)

Resuelve: *"¿qué pasó, cuándo, y en qué orden?"*. Es un registro cronológico de
acciones y decisiones, no de conocimiento — la diferencia con la memoria semántica es
que acá importa el *cuándo* y el *en qué contexto*, no solo el *qué*.

*Ejemplo propio:* el "log de escritura" que el roadmap pide para `agente_contenido`
("Registra el avance en un log de escritura"), y con mayor peso todavía en el
asistente IEC 62304 de gestión de cambios que tengo planificado — ahí la memoria
episódica no es una comodidad, es el requisito de trazabilidad de la norma.

### Memoria semántica (conocimiento del dominio)

Resuelve: *"¿cuáles son los hechos y reglas de este dominio?"*. Es conocimiento
relativamente estable — no cambia de una sesión a otra como sí lo hace un log — que el
agente consulta para fundamentar sus respuestas.

*Ejemplo propio:* el `GLOSARIO_DDD` de `hola_agente_sdk/agente_ddd_sdk.py`. Ya es una
memoria semántica en el sentido conceptual — el agente consulta una fuente de verdad
externa a su propio razonamiento antes de responder — aunque todavía esté hardcodeada
en un diccionario en vez de vivir en archivos reales.

---

## 3. Contexto vs. almacenamiento externo

La tentación obvia frente a un contexto de 200K o 1M tokens es pensar "si es tan
grande, meto todo ahí y me olvido del problema de la memoria". No funciona, por dos
razones distintas:

- **Costo**: cada token en el contexto se paga en cada llamada — aunque haya caching,
  hay un piso de costo que crece con lo que se manda.
- **Precisión**: un modelo con una ventana enorme no le presta la misma atención a
  cada parte de ella. Meter todo el conocimiento del dominio en cada prompt diluye lo
  relevante entre lo irrelevante.

Por eso el patrón real no es "contexto más grande", sino **contexto acotado + una capa
de recuperación** que trae del almacenamiento externo solo lo que hace falta para la
consulta puntual. La ventana de contexto no reemplaza a la memoria externa: es el lugar
donde la memoria externa se vuelca, momentáneamente, cuando hace falta.

---

## 4. RAG en una frase que me sirva para diseñar, no para repetir

RAG (retrieval-augmented generation) es el nombre que tiene el patrón de la sección
anterior cuando se aplica específicamente a traer texto relevante antes de generar una
respuesta. El patrón mínimo, sin la teoría completa:

**buscar → traer lo relevante → inyectar en el prompt → responder.**

Para `agente_contenido` esto se traduce en algo concreto: antes de redactar un
borrador de capítulo, el agente busca en las notas previas (por similitud semántica,
no por palabra clave exacta), trae los fragmentos más relevantes, los mete en el
contexto de esa llamada puntual, y recién ahí genera el texto. La búsqueda no
reemplaza al razonamiento del modelo — lo alimenta con lo que el modelo no podía saber
de otra forma.

---

## 5. Checkpointing y resumption

Dos patrones de diseño que aparecen apenas la memoria deja de ser solo "guardar
información" y empieza a ser "poder retomar un proceso interrumpido":

- **Checkpointing**: guardar el estado del agente en puntos intermedios del trabajo,
  no solo al final. Permite inspeccionar qué sabía el agente en un momento dado, y es
  la base de cualquier trazabilidad seria.
- **Resumption**: retomar la ejecución desde un checkpoint guardado, en vez de
  arrancar de cero.

Esto conecta directo con mi interés en IEC 62304: un sistema de gestión de cambios que
no puede mostrar en qué estado estaba una decisión en un momento dado, o que pierde el
hilo si el proceso se corta a mitad de camino, no sirve para auditoría. Memoria
episódica + checkpointing es, en los hechos, la misma necesidad vista desde dos
ángulos distintos — el log registra qué pasó, el checkpoint permite volver a pararse
ahí.

---

## 6. Preguntas abiertas

1. ¿Obsidian como fuente de memoria semántica vía integración directa, o simplemente
   archivos Markdown planos leídos del filesystem? ¿Qué gano y qué pierdo con cada
   opción para el caso de `agente_contenido`?

2. ¿Qué motor de memoria vectorial tiene sentido para un laboratorio de este tamaño —
   algo tan simple como embeddings + búsqueda por coseno en memoria, o ya vale la pena
   una base vectorial real (Chroma, similar)?

3. Para la memoria episódica: ¿un archivo de log estructurado (JSON Lines, por
   ejemplo) alcanza para lo que necesito, o el requisito de trazabilidad de IEC 62304
   empuja directamente a algo con más garantías (SQLite, por ejemplo)?

4. ¿Cómo se decide, en cada llamada, *qué* de la memoria de largo plazo es relevante
   para esa consulta puntual? ¿Es el propio modelo el que decide buscar (vía tool
   use), o hay una capa de recuperación previa que corre siempre?

5. ¿Checkpointing implica guardar el historial completo de mensajes en cada punto, o
   solo el estado mínimo necesario para reconstruir dónde estaba el agente?

---

## 7. Entregable de esta etapa

**Documento a completar:** este mismo archivo, enriquecido con:
- Respuestas (parciales o definitivas) a las preguntas abiertas de la sección 6
- La decisión de diseño tomada para `agente_contenido` antes de escribir el prototipo
- Al menos un ejemplo real de cada tipo de memoria ya implementado en código, no solo
  descripto en teoría

**Criterio de completitud:** poder explicar, sin notas, por qué la API es stateless y
qué implica eso para el diseño de un agente, distinguir los cuatro tipos de memoria
con un ejemplo propio de cada uno, y justificar en una frase por qué RAG no es "más
contexto" sino "contexto más enfocado".

---

*Última actualización: Agosto 2026 | Etapa: 3 de 4 | Estado: borrador inicial*
