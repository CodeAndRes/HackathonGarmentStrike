# 🎭 Coreografía del Turno (Game Flow)

Este documento define la secuencia temporal y los estados por los que pasa cada turno en **Garment Strike**. El objetivo es garantizar una experiencia de usuario fluida y sincronizada tanto en la terminal como en el Dashboard Web.

## 🕒 Tiempos Base (Configurables)
*   `ui_sleep`: Tiempo de espera tras una acción (Defecto: 1.2s).
*   `llm_latency`: Latencia natural de la API o simulada (Offline: 0.5s).

---

## 🎬 Secuencia de un Movimiento

Cada intento de disparo sigue este flujo exacto:

### 1. Fase de Pensamiento (Thinking)
*   **Estado**: El motor identifica al agente activo.
*   **Acción**: Se envía el estado "PENSANDO..." a las interfaces.
*   **Visual**: El Dashboard muestra el cursor parpadeante en telemetría. La terminal muestra "[Agente] Pensando...".
*   **Pausa**: `llm_latency` (La propia espera de la respuesta del modelo).

### 2. Fase de Decisión (Decision)
*   **Estado**: El motor recibe la coordenada y el razonamiento.
*   **Acción**: Se actualiza la telemetría con el razonamiento real (efecto máquina de escribir).
*   **Visual**: Se muestra la estrategia y el objetivo (cursor de apuntado en el tablero web).
*   **Pausa**: `sleep(0.5s)` (Para permitir leer el inicio del razonamiento).

### 3. Fase de Impacto (Execution)
*   **Estado**: El motor aplica el movimiento al tablero.
*   **Acción**: Se calcula el resultado (AGUA, IMPACTO o HUNDIDO).
*   **Visual**: 
    *   **Dashboard**: La celda flashea y cambia al icono correspondiente (Holograma/Prenda).
    *   **Terminal**: Se imprime la línea de log con el resultado resaltado.
*   **Pausa**: `sleep(ui_sleep)` (Pausa crítica para digerir el resultado antes de la siguiente acción).

### 4. Fase de Transición (Transition)
*   **Estado**: Verificación de "Golden Rule" (¿Repite turno?).
*   **Acción**: 
    *   Si es IMPACTO/HUNDIDO: El motor vuelve al paso 1 con el mismo agente.
    *   Si es AGUA/ERROR: `game.switch_turn()` y cambio de color en la interfaz.
*   **Pausa**: `sleep(0.3s)` (Pequeño respiro antes de que el siguiente equipo tome el control).

---

## 📊 Resumen de Esperas (Ejemplo con ui_sleep=1s)

| Fase | Acción Visual | Duración |
| :--- | :--- | :--- |
| **Inicio** | "Agente A está analizando..." | ~0.5s (Latencia) |
| **Apuntado** | "Estrategia: Flanco Norte | Objetivo: B4" | **sleep(0.5s)** |
| **Resultado** | "¡IMPACTO! Prenda localizada en B4" | **sleep(1.0s)** |
| **Siguiente** | Cambio de equipo o repetición | **sleep(0.3s)** |

---

> [!IMPORTANT]
> Esta coreografía debe ser **idéntica** para todas las UIs. El motor es quien dicta el ritmo a través de estos `sleeps`, asegurando que el Dashboard Web (que funciona por polling/ws) tenga tiempo de capturar y mostrar cada estado intermedio.
