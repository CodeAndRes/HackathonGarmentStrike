# Mission: Fase 3 — Optimización y Portabilidad
**ID**: MISSION-F3-OPTIMIZATION-PORTABILITY  
**Primary Agent**: `@supply-optimizer`, `@supply-dev`  
**Branch**: `feature/optimization-portability`  
**Depends on**: MISSION-F2-ELASTIC-TESTS [COMPLETED]

---

## 🎯 Objective
Reducir el consumo de tokens en celdas prohibidas, soportar modelos mixtos para partidas heterogéneas y preparar el repositorio (README) para el uso público durante el hackathon.

## 🚀 Tasks

### F3.1 — Comprimir celdas prohibidas (`@supply-optimizer`) ✅ COMPLETED
**File**: `core/engine.py`, `core/llm_client.py`, `core/prompts.py`

**Implemented:**
- **Range compression**: `Board._compress_coords()` collapses consecutive coordinates into ranges (e.g. `A1, A2, A3, A4, A5` → `A1-A5`), reducing token count by ~60% in late-game prompts.
- **Semantic categorization**: `grid_text_minimal()` now separates board state into `ACTIVE HITS (hunt nearby!)`, `SUNK (ignore)`, and `MISS` categories — giving the LLM actionable context instead of a flat dump.
- **Removed redundant forbidden list**: The `USER_PROMPT_TEMPLATE` no longer includes a separate "DO NOT SHOOT" section (the board state already encodes this). Server-side validation of `forbidden_coords` remains intact.
- **16 new tests** added: `TestCompressCoords` (10 tests) + `TestGridTextMinimal` (6 tests).
### F3.2 — Modelos mixtos por jugador (`@supply-dev`) ✅ COMPLETED
**File**: `main.py`, `core/tournament.py`

**Implemented:**
- **CLI**: `--model-a MODEL` and `--model-b MODEL` flags added to `play` subcommand. When only `--model` is given, both teams share it. When `-a` and `-b` differ, two separate `LLMClient` instances are created.
- **`run_match()`**: Accepts `LLMClient | dict[str, LLMClient]`. The match loop resolves `active_client = llm_clients[current]` per turn.
- **Interactive menu**: Option 4 now offers a sub-menu: (a) same model for both teams, (b) different model per team. The summary screen shows both models when they differ.
- **Backward compatible**: All existing callers (quick match, tournament) continue to work with a single model.

### F3.3 — README para el hackathon (`@supply-dev`) ✅ COMPLETED
**File**: `README.md`

**Implemented:**
- Added a new section for the Interactive Menu (`python main.py` with no args).
- Added explicit instructions and links for obtaining API keys for Groq, Gemini, OpenAI, and Ollama.
- Updated the CLI Reference to show mixed model parameters (`--model-a` and `--model-b`).

### F3.4 — Fijar tamaño de terminal (`@supply-optimizer`) ✅ COMPLETED
**File**: `core/visualizer.py`

**Implemented:**
- Added `os.get_terminal_size()` / `console.size` check in `GameDashboard.start()`.
- If the terminal is smaller than 90x24, it issues a yellow warning advising the player to resize the terminal before starting the Live dashboard.

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
