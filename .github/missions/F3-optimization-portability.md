# Mission: Fase 3 — Optimización y Portabilidad
**ID**: MISSION-F3-OPTIMIZATION-PORTABILITY  
**Primary Agent**: `@supply-optimizer`, `@supply-dev`  
**Branch**: `feature/optimization-portability`  
**Depends on**: MISSION-F2-ELASTIC-TESTS [COMPLETED]

---

## 🎯 Objective
Reducir el consumo de tokens en celdas prohibidas, soportar modelos mixtos para partidas heterogéneas y preparar el repositorio (README) para el uso público durante el hackathon.

## 🚀 Tasks

### F3.1 — Comprimir celdas prohibidas (`@supply-optimizer`)
**File**: `core/llm_client.py`, `core/prompts.py`

Actualmente, las coordenadas prohibidas se envían como una lista plana o conjunto que puede ser muy largo de tokenizar.
- Agrupar prohibidas por categoría (ej: "Agua/Miss", "Tocado/Hit", "Hundido/Sunk") para un mapa mental más claro para el LLM y que gaste menos tokens.

### F3.2 — Modelos mixtos por jugador (`@supply-dev`)
**File**: `main.py`, `core/tournament.py`

- Permitir pasar `--model-a` y `--model-b` (en vez de un solo `--model`) para enfrentar modelos (e.g. GPT-4 vs Llama3).
- Actualizar el menú interactivo para permitir seleccionar el modelo para el Equipo A y el Equipo B por separado.
- Modificar `run_match()` para instanciar (o utilizar dinámicamente) un `target_model` adecuado a cada agente.

### F3.3 — README para el hackathon (`@supply-dev`)
**File**: `README.md`

- Instrucciones claras y amigables de instalación (`pip install -r requirements.txt`).
- Guía de cómo obtener claves API para los distintos modelos soportados (Groq, Gemini, Ollama locales, OpenAI).
- Explicación de la estructura de configuración requerida para cada equipo (`agentes/<equipo>/...`).
- Ejemplo claro de comando de CLI (y aviso sobre el menú interactivo).

### F3.4 — Fijar tamaño de terminal (`@supply-dev`)
**File**: `core/visualizer.py`

- Asegurarse de que el dashboard Rich no se rompa si el terminal es muy pequeño, o añadir un check rápido en `GameDashboard.start()` que compruebe `os.get_terminal_size()` o la API de console de Rich y emita un warning de "Redimensiona tu consola para ver correctamente la partida".

---

## ✅ Verification Gate
- [ ] `python main.py play` soporta y ejecuta usando modelos diferenciados.
- [ ] La traza de logs de LLM confirma que la sección prohibitiva del prompt está comprimida.
- [ ] `README.md` contiene toda la información necesaria para un participante externo.
- [ ] Todos los tests siguen pasando (`python -m pytest tests/ -v`).

---
**Status**: [PENDING]  
**Assigned to**: @supply-optimizer + @supply-dev  
**Depends on**: MISSION-F2-ELASTIC-TESTS [COMPLETED]  
**Approval Required**: No
