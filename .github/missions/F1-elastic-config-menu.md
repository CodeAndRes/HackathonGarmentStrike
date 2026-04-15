# Mission: Fase 1 — Motor Elástico + Menú de Configuración
**ID**: MISSION-F1-ELASTIC-CONFIG  
**Primary Agent**: `@supply-dev`  
**Support**: `@supply-qa` (post-implementación)  
**Branch**: `feature/elastic-config-menu`

---

## 🎯 Objective
Completar la propagación de `ship_sizes` por todo el stack y añadir una pantalla de configuración de partida al menú interactivo.

## 🚀 Tasks

### F1.1 — Validación Pydantic dinámica
**File**: `core/llm_client.py`, `core/tournament.py`

El validador `AgentMove.validate_coordinate` usa una regex fija `[A-J](10|[1-9])` que acepta coordenadas fuera de tableros pequeños (ej: `J10` en un 6×6).

**Solución recomendada**: Mover la validación de rango al punto de consumo en `tournament.py`, justo después de parsear la respuesta del LLM. Añadir un check:
```python
valid_cols = set(target_board.cols)
valid_rows = set(target_board.rows)
col, row = move.coordenada[0], int(move.coordenada[1:])
if col not in valid_cols or row not in valid_rows:
    raise ValueError(f"Coordenada {move.coordenada} fuera del tablero {board_size}x{board_size}")
```

### F1.2 — Propagación de `ship_sizes`
**File**: `core/engine.py`

Completar la parametrización que fue revertida manualmente:
- `Board.__init__`: almacenar `self.ship_sizes = sorted(ship_sizes or REQUIRED_SHIP_SIZES, reverse=True)`
- `Board._validate_placement()`: comparar contra `self.ship_sizes` en vez de `REQUIRED_SHIP_SIZES`
- `AlmacenParser.parse()` y `parse_with_status()`: propagar `ship_sizes` al `generate_random_layout()`
- `generate_random_layout()`: usar `ship_sizes` param en vez de `REQUIRED_SHIP_SIZES`

### F1.3 — Pantalla de Configuración de Partida
**File**: `main.py`

Refactorizar la opción 3 ("Partida Personalizada") del menú interactivo:

```
-- Configuración de Partida --
1. Tamaño del tablero [6-10] (actual: 10)
2. Configuración de cajas (actual: [5,4,3,3,2])
3. Máximo de turnos (actual: 50)
4. Modelo de IA (actual: groq/llama-3.1-8b-instant)
5. Seleccionar equipos
6. ▶ INICIAR PARTIDA
```

Requisitos:
- Listar carpetas disponibles en `agentes/` para selección de equipos.
- Validar `ship_sizes` contra `board_size` antes de iniciar.
- Mostrar resumen de configuración antes de confirmar.

### F1.4 — Validación de límites
**File**: `core/engine.py`

Añadir una función de validación centralizada:
```python
def validate_game_config(board_size: int, ship_sizes: list[int]) -> None:
    if not 6 <= board_size <= 10:
        raise ValueError(f"board_size debe ser entre 6 y 10, recibido: {board_size}")
    if any(s > board_size for s in ship_sizes):
        raise ValueError(f"Ningún barco puede ser mayor que el tablero ({board_size})")
    if any(s < 2 for s in ship_sizes):
        raise ValueError(f"Tamaño mínimo de barco es 2")
    total_cells = sum(ship_sizes)
    max_cells = (board_size * board_size) // 2
    if total_cells > max_cells:
        raise ValueError(f"Total de celdas ({total_cells}) excede el 50% del tablero ({max_cells})")
```

### F1.5 — Limpiar docstrings y comentarios
**Files**: `core/engine.py`, `core/tournament.py`
- Actualizar docstring línea 7 de engine.py: quitar "sizes 5,4,3,3,2" → "configurable via ship_sizes"
- Eliminar comentario duplicado en tournament.py línea 233-234.

---

## ✅ Verification & Quality Gate
- [ ] `python main.py` → opción 3 → permite configurar tablero, cajas y turnos.
- [ ] `python main.py play --ship-sizes 3,2,2 --board-size 6 --no-visual` completa sin errores.
- [ ] `generate_random_layout(size=6, ship_sizes=[3,2,2])` genera 3 barcos válidos.
- [ ] El LLM no puede disparar fuera del rango del tablero activo.
- [ ] `python -m pytest tests/ -v` → todos los tests existentes siguen pasando.

## 📡 Reverse Communication
1. **Status Pulse**: Actualizar `Status` abajo (PENDING → IN_PROGRESS → COMPLETED/FAILED).
2. **Mission Log**: Crear `.github/missions/F1-ELASTIC-CONFIG-LOG.md`.
3. **Closing Report**: Añadir sección `## Outcome` en este archivo.

---

## 🔀 Integration
- Merge `feature/elastic-config-menu` → `main` tras pasar todos los checks.
- Eliminar la rama después del merge.

---
**Status**: [COMPLETED]  
**Assigned to**: @supply-dev  
**Approval Required**: No (Auto-integrate on test success)
