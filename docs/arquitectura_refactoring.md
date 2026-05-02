# 🏗️ Master Plan: Evolución Arquitectónica de Garment Strike

**Rol Asumido:** `SupplyPM` (Project Manager / Arquitecto)
**Objetivo:** Diseñar la arquitectura para escalar el juego hacia un entorno interactivo, retransmitible y accesible para humanos, sin romper la robustez del motor actual.

---

## 1. Reflexión: ¿Seguir igual o cambiar de Framework?

### Análisis de la situación actual
Actualmente usamos **FastAPI** para inyectar HTML/Vanilla JS y manejar un WebSocket global. Es un diseño monolítico rápido, pero las nuevas necesidades (Humano vs Máquina, UI de Drag & Drop para crear agentes, múltiples vistas según el rol) exigen manejo de estado complejo en el cliente.
Intentar hacer un Drag & Drop de barcos, validación de colisiones en tiempo real y formularios dinámicos con Vanilla JS acabará en un código inmanejable.

### Veredicto Arquitectónico: "Decoupled Stack" (Backend Python + Frontend Moderno)
- **Backend (Se queda en Python/FastAPI):** Python es innegociable para integrar modelos LLM, validación de reglas pesadas y orquestación. Seguiremos usando FastAPI, pero lo refactorizaremos para que sea una **API pura** (REST + WebSockets Pub/Sub).
- **Frontend (Migración a Framework Moderno):** Propongo introducir **React (Next.js o Vite) o Vue/Svelte**. Esto trivializa la gestión del estado (ej. saber si soy el jugador o el espectador) y nos da librerías maduras para el "Drag & Drop" del creador de agentes.

---

## 2. El Futuro del Modo Terminal

¿Vale la pena mantener el modo consola visual (Rich)?
**Veredicto: Degradar a herramienta de CI/CLI para Devs.**
Mantener la paridad de features entre la consola visual y la Web será un lastre. El menú interactivo de la terminal debe quedarse exclusivamente para:
- Ejecutar validaciones rápidas (`python main.py validate`).
- Correr matches de test sin UI (`python main.py play --headless`).
- La visualización principal, los torneos y las partidas humanas deben ocurrir 100% en la Web.

---

## 3. Refactoring Conceptual por Funcionalidades

### A. Facilitar la Creación de Agentes (Agent Builder UI)
Actualmente, los usuarios editan archivos `.md` a mano, lo que propicia errores de sintaxis o solapamiento de cajas.
**La Nueva Solución:** Una ruta web `/builder`.
1. **Paso 1:** Input para "Nombre del Equipo".
2. **Paso 2:** Un Grid interactivo de 10x10. El jugador arrastra sus 5 cajas desde un menú lateral al tablero. El frontend valida que no se solapen al instante.
3. **Paso 3:** Un área de texto grande para redactar el System Prompt (Estrategia).
4. **Acción:** Al pulsar "Guardar", el frontend envía un JSON a FastAPI. El backend genera y guarda automáticamente los archivos `equipo.md` y `equipo.almacen.md` en la carpeta `torneo/`.

### B. Modo Retransmisión (Broadcasting M vs M)
Pasaremos de un único WebSocket global a un sistema de **Salas (Rooms)**.
- Cuando se lanza una partida, el backend le asigna un ID (ej: `MATCH-42`).
- Las pantallas gigantes o PCs de la audiencia se conectan a la URL: `http://servidor/watch/MATCH-42`.
- El backend retransmite a todos los clientes suscritos a esa sala el estado completo (ambos tableros visibles, logs de razonamiento).

### C. Modo Jugable: Humano vs Máquina
El motor actual asume que los dos jugadores son funciones `llm_client.get_move()`. El refactoring implica transformar el motor de juego en un sistema impulsado por eventos (**Event-Driven Engine**).
- **El Humano** se conecta a `http://servidor/play/MATCH-42`.
- Recibe un estado ofuscado (ve su tablero completo, pero el del rival solo muestra agua o impactos).
- Cuando el Humano hace clic en una celda (ej: "C4"), el frontend envía un mensaje WebSocket al backend.
- El motor procesa el turno, y entonces llama al agente LLM para que responda.
- *Bonus:* El Humano podrá leer el razonamiento táctico que hace la Máquina en tiempo real mientras juega contra ella.

---

## 4. Roadmap de Refactorización (Pasos Sugeridos)

Si decides seguir este camino, no tocaremos todo a la vez. Lo haremos en fases para asegurar estabilidad:

1. **Fase 1: API de Salas (Backend).** Extraer la lógica de `core/engine.py` para que soporte IDs de partida, desconectando la UI actual temporalmente para que el backend funcione como un motor puro.
2. **Fase 2: Init Frontend Moderno.** Levantar el esqueleto de React/Vue en una carpeta `web/` y conectar el WebSocket básico.
3. **Fase 3: Agent Builder.** Construir la interfaz de Drag & Drop y el guardado de archivos para matar el problema de la configuración manual de inmediato.
4. **Fase 4: Vistas de Partida.** Implementar la vista del Humano (clicable y ofuscada) y la vista de Retransmisión (Dashboard táctico XL).

¿Qué te parece esta visión arquitectónica? ¿Quieres que empecemos por la Fase 1 o prefieres pivotar alguna de las ideas?
