# Copilot Mission: Dynamic Ship Configuration
**ID**: MISSION-2026-04-13-DSC  
**Primary Agent**: `supply-dev`  
**Standard**: Copilot Agent Protocol v4.2 (April 2026)

## 🎯 Context & Objective
The current engine uses hardcoded ship sizes `[5, 4, 3, 3, 2]`. This mission requires making these sizes fully parameterizable across the entire stack (CLI, Settings, Tournament, and Engine).

## 🚀 Mission Directives

### 1. Workspace Initialization
- Create a new Git branch named `feature/parameterized-ship-config`.
- Baseline check: Ensure all 96 existing tests pass before starting.

### 2. Implementation Scope
- **Settings**: Add `ship_sizes: [5, 4, 3, 3, 2]` to the `engine` segment of `settings.yaml`.
- **Engine**: Refactor `Board` and `AlmacenParser` in `core/engine.py` to accept dynamic lists of integers.
- **CLI**: Add `--ship-sizes` argument to `main.py`.
- **Tournament**: Propagate configuration to ensure 1v1 and Round-Robin matches use the same parameters.
- **Validation**:
  - Max ship size must be `<= board_size`.
  - Minimum ship size must be `>= 2`.
  - Total ship cells must not exceed 50% of the board area.

### 3. Verification & Quality Gate
- [ ] Run `pytest tests/` and ensure 100% pass rate.
- [ ] Execute a smoke test match with a custom configuration: `board-size 6`, `ship-sizes [3,2,2]`.

### 4. Integration
- Once all verification steps are marked as completed and stable:
  - Merge `feature/parameterized-ship-config` into `main`.
  - Delete the feature branch.

## ⚠️ Constraints
- Maintain backward compatibility: if no sizes are provided, default to `[5, 4, 3, 3, 2]`.
- All user-facing terminal output must use "Prenda/Pedido" terminology.

---
**Status**: [IN_PROGRESS]  
**Assigned to**: @supply-dev  
**Approval Required**: No (Auto-integrate on test success)

## 📡 Reverse Communication (Standard 2026)
1. **Status Pulse**: El agente debe actualizar el campo `Status` arriba (PENDING -> IN_PROGRESS -> COMPLETED/FAILED).
2. **Mission Log**: Crear un archivo `.github/missions/DSC-Parameterization-LOG.md` con el histórico de decisiones técnicas.
3. **Closing Report**: Al terminar, el agente debe generar un comentario en el PR o añadir una sección `## Outcome` en este mismo archivo detallando los resultados de los tests.
