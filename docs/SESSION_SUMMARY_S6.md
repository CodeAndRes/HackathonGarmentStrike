# Garment Strike - Session Summary (Session 6)

**Date**: April 12, 2026  
**Session Focus**: Tablero Dinámico, Desempate por Puntos & Auditoría  
**Status**: ✅ All features implemented and tested

---

## What Was Done

### 1. Tablero Dinámico (6×6 a 10×10) ✅

Refactorización completa del motor para eliminar todos los valores hardcodeados de 10×10.

| Componente | Cambio | Archivo |
|---|---|---|
| Constantes globales | `BOARD_COLS`/`BOARD_ROWS` → funciones `get_board_cols(size)`/`get_board_rows(size)` | `core/engine.py` |
| Board | Constructor acepta `size` param, genera `cols`/`rows` dinámicamente | `core/engine.py` |
| AlmacenParser | `parse()` y `parse_with_status()` aceptan `size`, regex flexibilizada | `core/engine.py` |
| Random Layout | `generate_random_layout(size)` ajusta tamaños de barco al tablero | `core/engine.py` |
| Visualizer | `render_board()` usa `board.cols` dinámico | `core/visualizer.py` |
| LLM Client | `board_size` inyectado en prompts del sistema | `core/llm_client.py` |
| Prompts | Rango de coordenadas dinámico (`A-F, 1-6` en vez de `A-J, 1-10`) | `core/prompts.py` |
| CLI | `--board-size N` (default desde `settings.yaml`) | `main.py` |
| Tournament | `board_size` propagado a carga de tableros y ejecución | `core/tournament.py` |

### 2. Desempate por Puntos al Límite de Turnos ✅

Cuando la partida alcanza `max_turns`, el ganador se decide por orden de prioridad:

1. **PUNTOS** — Más pedidos hundidos (barcos completos del rival)
2. **HITS** — Más prendas encajadas (impactos totales al rival)
3. **DEFENSA** — Menos impactos recibidos en el propio tablero
4. **EMPATE ABSOLUTO** — Solo si todos los criterios anteriores son idénticos

| Parámetro | Ubicación | Default |
|---|---|---|
| `max_turns` | `settings.yaml` + CLI `--max-turns` | 50 |

### 3. Optimización de Prompts del LLM ✅

**Problema detectado**: El modelo 8B (Llama 3.1) repetía disparos a coordenadas ya marcadas como agua, especialmente a partir del turno ~30.

**Solución implementada**:
- **Lista negra explícita**: Sección `### DO NOT SHOOT (already fired):` inyectada justo antes del comando, donde el modelo la ve con máximo peso de atención.
- **Rango dinámico**: `Command: Choose ONE coordinate (A-F, 1-6) NOT in the list above:` en vez del viejo `(A-J, 1-10)` hardcodeado.

### 4. Auditoría General & Corrección de Inconsistencias ✅

Se identificaron y corrigieron **6 incongruencias**:

| # | Severidad | Problema | Corrección |
|---|---|---|---|
| 1 | 🔴 Alta | Lógica de desempate duplicada y contradictoria entre `Game.is_over()` y `tournament.py` | Eliminada de `Game` — solo `tournament.py` decide |
| 2 | 🔴 Alta | Tercer criterio de desempate inerte (reutilizaba variables del criterio 2, código muerto) | Variables separadas: `hits_by_X` (ofensivo) vs `dmg_to_X` (defensivo) |
| 3 | 🔴 Alta | `MAX_TURNS = 120` hardcodeado en `Game` contradecía `max_turns=50` de settings | Eliminado. Solo `tournament.py` controla el límite |
| 4 | 🔴 Alta | `timeout_winner` no se propagaba al `MatchRecord` — log decía "Alpha gana" pero CLI decía "EMPATE" | Variable `timeout_winner` separada, combinada con `natural_winner` al final |
| 5 | 🟡 Media | Docstring del módulo decía "10×10" | Actualizado a "dynamic 6×6–10×10" |
| 6 | 🟢 Baja | `alphabet="ABCDEFGHIJ"` en `Ship._validate_contiguous` parecía hardcodeado | Comentario aclaratorio (es correcto: solo se usa para index math) |

### 5. Corrección de Fallbacks de Emergencia ✅

| Punto de fallback | Bug previo | Corrección |
|---|---|---|
| `AlmacenParser` (archivo ilegible) | `generate_random_layout()` sin `size` | Añadido `size=size` |
| `AlmacenParser` (coordenadas fuera de rango) | `generate_random_layout()` sin `size` | Añadido `size=size` |
| `tournament.py` (LLM falla) | Iteraba `"ABCDEFGHIJ"` y `range(1,11)` hardcodeados | Usa `target_board.cols` / `target_board.rows` |
| `visible_state()` | `.index(col)` podía crashear con `ValueError` en tableros pequeños | Envuelto en `try-except` |

---

## Files Changed

```
core/engine.py          Major refactor: dynamic board, removed Game.MAX_TURNS & duplicate tiebreaker
core/tournament.py      Tiebreaker logic, max_turns param, winner propagation fix, dynamic fallback
core/llm_client.py      board_size injection, forbidden_text in prompts, dynamic range_text
core/prompts.py         Dynamic coordinate range + forbidden coordinates section
core/visualizer.py      Dynamic column rendering from board instance
main.py                 --board-size and --max-turns CLI arguments
settings.yaml           Added board_size: 10, max_turns: 50
```

---

## Test Results

Partida de prueba 6×6 ejecutada con éxito:

```
[T  50] Alpha           -> A3   | Prenda encajada  | lat: 0.32s

[SISTEMA] Límite de 50 turnos alcanzado. Aplicando desempate por puntos.
[SISTEMA] Victoria concedida a Alpha por PUNTOS.

Ganador: Alpha
Turnos totales: 50
Disparos: Alpha=26  |  Beta=24
```

**Verificaciones**:
- ✅ Parser detecta `F7` fuera del 6×6 y genera layout aleatorio válido
- ✅ LLM recibe rango correcto `A-F, 1-6`
- ✅ Lista negra de celdas disparadas inyectada en el prompt
- ✅ Desempate por PUNTOS funciona y se propaga al `MatchRecord`
- ✅ Sin crashes ni `index out of range`
- ✅ Fallback de emergencia genera coordenadas dentro del tablero actual

---

## Backlog Items Resolved

- [x] Tamaño de tablero dinámico (6×6 a 10×10)
- [x] Separar el archivo de parámetros del de claves API key (`settings.yaml` vs `.env`)
- [x] Tiro forzado debería ser random pero excluyendo coordenadas ya atacadas
- [x] Posible envío de contexto mayor tras Fallback (implementado como `⚠️ CRITICAL` warning)

## Remaining Backlog

- [ ] Traducir en la respuesta del LLM los términos de Battleship a Logística
- [ ] Intentar fijar el tamaño de la pantalla del terminal
- [ ] Organizar todas las pruebas unitarias
- [ ] Que en los logs aparezca la fecha/hora y el modelo
- [ ] Explorar distintos modelos de IA para cada jugador
- [ ] Web Dashboard para visualización remota

---

## Context for Next Session

- **Engine**: Estable en tableros de 6×6 a 10×10. Todas las constantes globales eliminadas.
- **LLM**: Groq/Llama-3.1-8B-Instant funcionando con `api_sleep: 7.0`. El modelo repite coordenadas en partidas largas (~30+ turnos) — mitigado con la sección `DO NOT SHOOT`.
- **Architecture**: `Game` es ahora una máquina de estados pura. Toda la lógica de límite de turnos y desempate vive en `tournament.py`.
- **Next Focus**: Ejecutar torneo con varios equipos y validar el sistema de clasificación completo.
