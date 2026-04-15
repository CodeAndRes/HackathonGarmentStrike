# Mission: Fase 2 — Tests Elásticos + Logs Mejorados
**ID**: MISSION-F2-ELASTIC-TESTS  
**Primary Agent**: `@supply-qa`  
**Support**: `@supply-dev` (tareas F2.4, F2.5)  
**Branch**: `feature/elastic-tests-logging`  
**Depends on**: F1 must be COMPLETED first.

---

## 🎯 Objective
Refactorizar los tests para que soporten cualquier configuración dinámica y mejorar la trazabilidad de los logs.

## 🚀 Tasks

### F2.1 — Tests parametrizados del motor (`@supply-qa`)
**File**: `tests/test_engine.py`

- Refactorizar `_make_ships(ship_sizes, board_size)` para aceptar parámetros dinámicos.
- Refactorizar `_make_valid_board(ship_sizes, board_size)` igual.
- Añadir `@pytest.mark.parametrize` con las siguientes configuraciones:
  - `(10, [5,4,3,3,2])` — Estándar
  - `(6, [3,3,2])` — Mínimo viable
  - `(8, [4,3,2,2])` — Intermedio
  - `(6, [2,2])` — Ultra mínimo

### F2.2 — Tests del AlmacenParser dinámico (`@supply-qa`)
**File**: `tests/test_engine.py`

- Test: `parse_with_status(file, size=6, ship_sizes=[3,2,2])` genera layout correcto.
- Test: Archivo con barcos de tamaño 5 en tablero 6×6 → fallback aleatorio.
- Test: `ship_sizes=[]` → error controlado.
- Test: Ship mayor que board_size → error controlado.

### F2.3 — Tests de validación Pydantic dinámica (`@supply-qa`)
**File**: `tests/test_llm_client.py`

- Test: `AgentMove("G5")` en tablero 6×6 → rechazado.
- Test: `AgentMove("F6")` en tablero 6×6 → aceptado.
- Test: `AgentMove("J10")` en tablero 10×10 → aceptado.
- Depende de cómo F1.1 implemente la validación dinámica.

### F2.4 — Logs con timestamp y modelo (`@supply-dev`)
**File**: `core/tournament.py`

Formato actual:
```
[T   5] Alpha -> E5 | Prenda perdida | lat: 0.51s
```

Formato objetivo:
```
[2026-04-15 18:30:12] [groq/llama-3.1-8b] [T   5] Alpha -> E5 | Prenda perdida | lat: 0.51s
```

### F2.5 — Terminología logística completa (`@supply-dev`)
**Files**: `core/tournament.py`, `core/visualizer.py`

Verificar que TODOS los puntos de salida usan el `LOGISTICS_MAP`:
- `match_turns.log` ✅ (ya usa)
- Dashboard visual → verificar
- Prompt del LLM → verificar que no se inyecta "HIT/SUNK" en texto visible al usuario

---

## ✅ Verification Gate
- [x] `python -m pytest tests/ -v` → 100% pass con `ship_sizes=[3,3,2]` en settings.yaml.
- [x] `python -m pytest tests/ -v` → 100% pass con `ship_sizes=[5,4,3,3,2]` en settings.yaml.
- [x] Los tests NO importan ni usan `REQUIRED_SHIP_SIZES` directamente.
- [x] `match_turns.log` muestra timestamp + modelo en cada línea.

---
**Status**: [COMPLETED]  
**Assigned to**: @supply-qa + @supply-dev  
**Depends on**: MISSION-F1-ELASTIC-CONFIG [COMPLETED]  
**Approval Required**: No
