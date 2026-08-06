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

## Cómo se relacionan los tres diagramas

El diagrama 1 (ReAct) describe el *comportamiento* — qué pasa en cada paso. El
diagrama 2 (estructura del agente) describe los *componentes* — qué piezas hacen
falta para que ese comportamiento sea posible. El diagrama 3 (harness) describe
*quién construye esas piezas* — vos a mano, un SDK, o un servicio gestionado. Los
tres capturan el mismo sistema desde ángulos distintos: proceso, arquitectura, y
responsabilidad de implementación.

---

*Creado: Agosto 2026 | Referencia visual de Etapas 1–2 | Se actualiza si los
conceptos base cambian en `modelo_mental_agentico.md`*
