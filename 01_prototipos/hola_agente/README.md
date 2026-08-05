# hola_agente — Prototipo DDD

> Primer agente funcional del laboratorio. Demuestra el ciclo ReAct con tool use real.

**Etapa:** 2 — Primer agente funcional  
**Estado:** completo  
**Tiempo estimado para ejecutarlo:** 5 minutos

---

## Qué hace este agente

Dado un concepto de Domain-Driven Design, el agente produce:

1. **Definición** — técnica, con metáfora y ejemplo concreto
2. **Pregunta socrática** — para usar en clase, sin respuesta obvia
3. **Código Python** — pedagógico, con nombres del dominio

El agente decide por sí mismo en qué orden usar las herramientas y cómo integrar los resultados.

---

## Cómo ejecutarlo

```bash
# 0. (una sola vez, desde la raíz del proyecto) crear el entorno y las dependencias
cd ../..
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y completar ANTHROPIC_API_KEY en .env

# 1. Ejecutar
cd 01_prototipos/hola_agente
python agente_ddd.py
```

Para probar con otro concepto, cambiá esta línea al final del archivo:

```python
concepto = "Agregado"   # → "Entidad", "Value Object", "Repositorio", etc.
```

---

## Qué observar mientras corre

El agente imprime cada paso del ciclo ReAct en consola:

```
[Ciclo 1] RAZONANDO  — consultando al modelo...
[Ciclo 1] ACTUANDO   — generar_definicion({'concepto': 'Agregado'})
[Ciclo 1] OBSERVANDO — generar_definicion devolvió 312 chars

[Ciclo 2] RAZONANDO  — consultando al modelo...
[Ciclo 2] ACTUANDO   — crear_pregunta_socratica({'concepto': 'Agregado'})
...
[Ciclo N] RESPUESTA FINAL generada luego de N ciclos
```

Notá que el número de ciclos varía: el modelo decide cuántas iteraciones necesita.

---

## Arquitectura del código

```
agente_ddd.py
│
├── TOOLS_SCHEMA   → Descripción de las herramientas para el modelo
│                    (el modelo las lee, no las ejecuta)
│
├── TOOLS_IMPL     → Implementación real en Python
│                    (funciones que se ejecutan cuando el modelo las pide)
│
├── TOOLS_IMPL     → Dispatcher nombre → función
│
└── react_loop()   → El ciclo principal:
                      while True:
                        llamar modelo →
                          si tool_use: ejecutar tool, agregar al historial
                          si end_turn: retornar respuesta final
```

---

## Decisiones de diseño

**¿Por qué las tools llaman a Claude internamente?**  
Cada tool hace una llamada Claude con un prompt muy específico. Esto es un patrón válido: un agente puede tener sub-llamadas al modelo para tareas especializadas. En el siguiente prototipo, algunas tools leerán archivos de Obsidian en lugar de llamar al modelo.

**¿Por qué `claude-haiku` y no `claude-sonnet`?**  
Para pruebas de aprendizaje, haiku es más rápido y económico. La arquitectura es idéntica con cualquier modelo.

**¿Por qué el historial se pasa completo en cada ciclo?**  
Así funciona la API de Claude: es stateless. El "estado" del agente vive en la lista `messages` que vos mantenés y pasás en cada llamada. Esto es importante para entender dónde vive la memoria en Etapa 3.

---

## Aprendizajes clave

- El modelo **no ejecuta código**. Solo dice "quiero llamar a X con args Y".
- El loop `while True` es el ciclo ReAct: el modelo controla cuántas iteraciones hace.
- El protocolo de tool use requiere que los resultados vuelvan como mensajes `user`.
- El `tool_use_id` conecta cada resultado con la llamada que lo originó.

---

## Próximo paso (Etapa 3)

Convertir `generar_definicion()` para que lea notas de Obsidian antes de generar,  
incorporando memoria de largo plazo al ciclo.
