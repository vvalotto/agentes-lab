# Diagramas de conceptos — síntesis visual

> Documentación visual de los conceptos desarrollados en Etapas 1 y 2. No reemplaza
> a `modelo_mental_agentico.md` ni a los README de cada prototipo — es un resumen
> para repasar de un vistazo, con referencias a dónde profundizar cada cosa.

---

## 1. El ciclo ReAct

El corazón de cualquier agente: razonar, actuar, observar, repetir hasta terminar.
Detalle completo en [`modelo_mental_agentico.md`](modelo_mental_agentico.md#3-el-ciclo-react).

```mermaid
flowchart LR
    O1["Observación<br/>(estado inicial / resultado previo)"] --> R["Razonamiento<br/>¿Qué sé? ¿Qué falta? ¿Qué hago?"]
    R --> A["Acción<br/>invoca una herramienta con parámetros"]
    A --> O2["Observación<br/>resultado de la herramienta"]
    O2 -.->|si falta info| R
    O2 -->|si ya alcanza| F["Respuesta final<br/>stop_reason == end_turn"]

    style F fill:#2d5a3d,color:#fff
```

**Dónde lo vi en código:** el `while True` de `react_loop()` en
[`hola_agente/agente_ddd.py`](../../01_prototipos/hola_agente/agente_ddd.py) — cada
vuelta del loop es exactamente uno de estos ciclos, con la diferencia de que un solo
ciclo puede disparar varias acciones (tool calls) antes de volver a razonar.

---

## 2. Estructura de un agente

Un agente no es "un LLM con más pasos" — es un sistema de cuatro piezas que se
retroalimentan. Sacar cualquiera de las cuatro rompe la definición: sin herramientas
solo hay texto, sin memoria cada paso arranca de cero, sin ciclo no hay repetición.

```mermaid
flowchart TB
    C(["Ciclo de ejecución<br/>razona → actúa → observa → repite"])

    M["Modelo de lenguaje<br/>el motor de razonamiento<br/>(Claude)"]
    H["Herramientas<br/>acciones en el mundo<br/>(buscar, leer, ejecutar)"]
    Mem["Memoria<br/>información entre pasos<br/>(corto/largo plazo, episódica, semántica)"]

    C --> M
    M -->|decide invocar| H
    H -->|resultado| C
    C <-->|lee / escribe| Mem
    M -->|consulta| Mem

    style C fill:#1e3a5f,color:#fff
```

**Dónde lo vi en código:** en `hola_agente_sdk/agente_ddd_sdk.py`, el `GLOSARIO_DDD`
es la Memoria (semántica, aunque hardcodeada), `buscar_termino_ddd` es la Herramienta,
`query(prompt, options)` es el Ciclo de ejecución — provisto por el SDK en vez de
escrito a mano — y Claude sigue siendo el Modelo en los tres casos.

---

## 3. Tipos de harness

El harness es el andamiaje que rodea al modelo y lo convierte en agente: decide
cuándo llamarlo, cómo ejecuta las tools, y qué historial mantiene. El motor (Claude)
es el mismo en los cuatro casos — lo que cambia es cuánto de ese andamiaje escribís
vos y cuánto viene dado.

```mermaid
flowchart TB
    Motor(["Motor: Claude<br/>(idéntico en los 4 casos)"])

    subgraph O1["1 · API directa + loop manual"]
        direction TB
        D1["Vos escribís:<br/>el while, el dispatcher de tools,<br/>todo el ciclo ReAct"]
    end

    subgraph O2["2 · API directa + Tool Runner"]
        direction TB
        D2["Vos escribís:<br/>solo las funciones de las tools<br/>(el loop lo da el SDK)"]
    end

    subgraph O3["3 · Claude Agent SDK"]
        direction TB
        D3["Vos escribís:<br/>prompt + opciones<br/>(harness completo: tools, MCP, sesiones)"]
    end

    subgraph O4["4 · Managed Agents"]
        direction TB
        D4["Vos escribís:<br/>config del agente<br/>(Anthropic corre el loop Y el contenedor)"]
    end

    Motor --> O1
    Motor --> O2
    Motor --> O3
    Motor --> O4

    D1 -.probado en.-> P1["hola_agente/"]
    D3 -.probado en.-> P3["hola_agente_sdk/"]
    D2 -.pendiente.-> P2["(no probado todavía)"]
    D4 -.pendiente.-> P4["(no probado todavía)"]

    style O1 fill:#2d5a3d,color:#fff
    style O3 fill:#2d5a3d,color:#fff
    style O2 fill:#4a4a1a,color:#fff
    style O4 fill:#4a4a1a,color:#fff
```

**La distinción que más importa:** las opciones 1, 2 y 3 dejan el *deployment* en tus
manos — vos corrés el proceso, donde sea que lo corras. Solo la opción 4 (Managed
Agents) gestiona también la infraestructura: ni siquiera hace falta un proceso
Python corriendo en tu máquina.

---

## 4. Anatomía de `TOOLS_SCHEMA`

`TOOLS_SCHEMA` es lo que el *modelo ve* de cada herramienta — nombres, descripciones
y parámetros. No es la implementación: es la declaración que le permite a Claude
decidir *cuándo* pedir una tool y *con qué argumentos*, sin ejecutar nada él mismo.
Cada elemento de la lista tiene la misma forma, sin importar qué haga la tool por
dentro.

```mermaid
flowchart TB
    T["Un elemento de TOOLS_SCHEMA<br/>(una herramienta declarada)"]

    N["name<br/>string — identificador único<br/>Claude lo usa para pedir esta tool específica"]
    D["description<br/>string — la ÚNICA señal que tiene Claude<br/>para decidir CUÁNDO usar esta tool"]
    S["input_schema<br/>JSON Schema — qué argumentos acepta"]

    T --> N
    T --> D
    T --> S

    ST["type: 'object'"]
    P["properties<br/>un campo por parámetro"]
    R["required<br/>array — qué parámetros son obligatorios"]

    S --> ST
    S --> P
    S --> R

    P1["concepto<br/>type: string<br/>description: 'El concepto DDD a ilustrar'"]
    P2["dominio<br/>type: string<br/>description: 'Dominio de negocio...'"]
    P --> P1
    P --> P2

    style D fill:#1e3a5f,color:#fff
    style R fill:#4a4a1a,color:#fff
```

**Ejemplo real:** la tool `generar_codigo` de
[`hola_agente/agente_ddd.py`](../../01_prototipos/hola_agente/agente_ddd.py) — dos
parámetros (`concepto`, `dominio`), ambos obligatorios según `required`.

**El punto que no es obvio a simple vista:** `TOOLS_SCHEMA` (lo que Claude *ve*) y
`TOOLS_IMPL` (lo que el código *ejecuta*) son dos estructuras separadas que conviven
en el mismo archivo, conectadas solo por el `name`. Claude nunca toca `TOOLS_IMPL`
— ese dispatcher es puro Python de tu lado. Esta separación es la misma que después
el Claude Agent SDK esconde detrás del decorador `@tool` en `hola_agente_sdk`: ahí
`TOOLS_SCHEMA` e implementación se declaran juntos, pero conceptualmente siguen
siendo las dos mismas piezas.

---

## Cómo se relacionan los cuatro diagramas

El diagrama 1 (ReAct) describe el *comportamiento* — qué pasa en cada paso. El
diagrama 2 (estructura del agente) describe los *componentes* — qué piezas hacen
falta para que ese comportamiento sea posible. El diagrama 3 (harness) describe
*quién construye esas piezas* — vos a mano, un SDK, o un servicio gestionado. El
diagrama 4 (`TOOLS_SCHEMA`) baja un nivel más y muestra la forma concreta de una
sola de esas piezas — la Herramienta del diagrama 2 — tal como Claude la percibe.
Los cuatro capturan el mismo sistema desde ángulos distintos: proceso, arquitectura,
responsabilidad de implementación, y detalle de una pieza puntual.

---

*Creado: Agosto 2026 | Referencia visual de Etapas 1–2 | Se actualiza si los
conceptos base cambian en `modelo_mental_agentico.md`*
