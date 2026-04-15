# ⚡ Garment Strike — AI Supply Chain Simulation

> **AI Hackathon** · April 2026
>
> A multi-agent Supply Chain simulation inspired by Battleship.
> Teams write a **Natural Language Strategy Manifesto** (`agent.md`) and let an LLM play for them.

---

## 🎮 Game Rules

| Concept | Detail |
|---|---|
| **Board** | 10 × 10 grid, columns A–J, rows 1–10 |
| **Pedidos (orders)** | 5 boxes of sizes **5, 4, 3, 3, 2** |
| **Shots** | "Prendas" (garments) thrown at coordinates |
| **HIT** | Lands on a box → **same agent shoots again** (Golden Rule) |
| **SUNK** | All cells of a box hit → **same agent shoots again** |
| **MISS** | Empty cell → turn passes to the other agent |
| **Win** | First to sink all 5 opponent orders wins |

---

## 📂 Project Structure

```
BT-Supply-Impulse/
├── core/
│   ├── engine.py          # Board logic, Ship, AlmacenParser, Game state machine
│   ├── llm_client.py      # LiteLLM connector, prompt builder, Pydantic output parser
│   ├── visualizer.py      # Rich terminal dashboard (dual boards + telemetry)
│   └── tournament.py      # Round-Robin runner, standings, JSON report
│
├── templates/
│   ├── agent_template.md  # Blank strategy manifesto for participants
│   └── almacen_template.md # Blank warehouse placement for participants
│
├── agentes/
│   └── ejemplo/           # Demo agent (Hunt & Target strategy)
│       ├── agent.md
│       └── almacen_equipo_ejemplo.md
│
├── tests/
│   ├── test_engine.py     # 40+ unit tests (board, ships, parsing, game rules)
│   └── test_llm_client.py # 25+ unit tests (coordinate validation, prompt builder)
│
├── main.py                # CLI entry point (play / tournament)
├── requirements.txt
├── .env.example           # API key template
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

Dependiendo del modelo que decidas usar, necesitarás una clave de API. Copia el archivo base y configúralo:
```bash
cp .env.example .env
```
Edita `.env` y añade tu clave. ¿Dónde conseguirlas?
- **Groq** (Rápido, gratis): [console.groq.com](https://console.groq.com/keys) (`GROQ_API_KEY`)
- **Google Gemini** (Gratis/De pago): [aistudio.google.com](https://aistudio.google.com/app/apikey) (`GEMINI_API_KEY`)
- **OpenAI** (De pago): [platform.openai.com](https://platform.openai.com/api-keys) (`OPENAI_API_KEY`)
- **Ollama** (Local, gratis): No necesita API Key. Simplemente instala [ollama.com](https://ollama.com) y ejecuta `ollama run llama3`.

### 3. Run the tests (no API key needed)

```bash
pytest tests/ -v
```

### 4. Lanzar el Menú Interactivo (Fácil)

La forma más sencilla de jugar o configurar partidas personalizadas (**incluyendo enfrentaiento de de modelos mixtos**) es sin pasar argumentos:

```bash
python main.py
```

### 5. Play a single match (CLI Avanzada)

```bash
python main.py play \
  --team-a "Alpha" \
  --agent-a agentes/ejemplo/agent.md \
  --almacen-a agentes/ejemplo/almacen_equipo_ejemplo.md \
  --team-b "Beta" \
  --agent-b agentes/ejemplo/agent.md \
  --almacen-b agentes/ejemplo/almacen_equipo_ejemplo.md
```

### 6. Run a full tournament

```bash
# Place each team's files in agentes/<team_name>/
python main.py tournament --agents-dir agentes/ --output tournament_results.json
```

---

## 🤖 How to Create Your Agent

### Step 1 — Strategy Manifesto (`agent.md`)

Copy `templates/agent_template.md` to your team folder and fill in your strategy.

The engine injects your **entire `agent.md`** into the LLM prompt on every turn.

Key sections to define:
- **Exploration pattern** (how to search an empty board)
- **Hunt protocol** (what to do after a HIT)
- **Golden Rules** (never shoot twice at the same cell, always valid JSON)

### Step 2 — Warehouse Placement (`almacen_equipo_X.md`)

Copy `templates/almacen_template.md` and set your pedido coordinates:

```
P1: A1 B1 C1 D1 E1    ← size 5, horizontal row 1
P2: A3 B3 C3 D3       ← size 4, horizontal row 3
P3: F5 F6 F7          ← size 3, vertical col F
P4: H8 I8 J8          ← size 3, horizontal row 8
P5: D7 D8             ← size 2, vertical col D
```

The parser accepts two formats: **key: coords** and **markdown table**.

### Step 3 — Register for tournament

```
agentes/
└── mi_equipo/
    ├── agent.md
    └── almacen_mi_equipo.md
```

### Optional — Copilot Project Builder Agent (session continuity)

This repository includes a GitHub-standard custom Copilot agent at:

`.github/agents/constructor-proyecto.agent.md`

Use it when you want to resume work in a new session with implementation + validation + clear handoff output.

Example prompt:

```text
Retoma el proyecto desde el ultimo estado y completa la siguiente tarea: [tu tarea].
Valida con pruebas relevantes y deja resumen de cambios, riesgos y siguientes pasos.
```

---

## 🔌 Supported LLM Models

Pasando el flag `--model` (o `--model-a` y `--model-b` para partidas mixtas), puedes usar cualquier formato soportado por [LiteLLM](https://docs.litellm.ai/docs/providers):

| Provider / Type | Example string | Notes |
|---|---|---|
| **Ollama (Local)** | `ollama/llama3` o `ollama/gemma4:e4b` | Tu propio modelo local (Requiere instalar y lanzar Ollama). Muy seguro y sin coste. |
| **Groq (Cloud rápida)** | `groq/llama-3.1-8b-instant` | Excelente para hackathons. Muy veloz. Poner `GROQ_API_KEY` en `.env`. |
| **Google Gemini** | `gemini/gemini-1.5-pro` | Poner `GEMINI_API_KEY` en `.env`. Cuidado con los límites de RPM. |
| **OpenAI** | `openai/gpt-4o` | Poner `OPENAI_API_KEY` en `.env`. |
| **Anthropic** | `anthropic/claude-3-5-sonnet-20241022` | Poner `ANTHROPIC_API_KEY` en `.env`. |

---

## 🏗️ Architecture

```
main.py  ──►  tournament.py  ──►  engine.py    (pure game state)
                    │
                    └──►  llm_client.py  ──►  LiteLLM  ──►  LLM Provider
                    │         │
                    │         └──►  agent.md   (strategy manifesto)
                    │
                    └──►  visualizer.py  ──►  Rich Terminal Dashboard
```

**Sub-Agent Roles (internal design):**

| Agent | Responsibility |
|---|---|
| Developer Agent | `engine.py` + `llm_client.py` core logic |
| Reviewer Agent | Golden Rule enforcement in `tournament.py:run_match()` |
| QA Agent | `tests/test_engine.py` + `tests/test_llm_client.py` |

---

## 📊 Tournament Results

After a tournament, `tournament_results.json` contains:

```json
{
  "partidas": [
    {
      "agente_a": "Alpha",
      "agente_b": "Beta",
      "ganador": "Alpha",
      "turnos_totales": 87,
      "disparos_a": 52,
      "disparos_b": 35,
      "disparos_invalidos_a": 0,
      "disparos_invalidos_b": 2
    }
  ],
  "clasificacion": {
    "Alpha": { "wins": 3, "losses": 0, "draws": 0, "total_shots": 142, "wasted_shots": 0 }
  }
}
```

---

## ⚙️ CLI Reference

```
python main.py [--model MODEL] [--no-visual] <command>

Commands:
  (none)      Starts interactive menu
  play        Single match
  tournament  Round-Robin tournament

play options:
  --team-a NAME     Name of team A
  --agent-a PATH    Path to team A's agent.md
  --almacen-a PATH  Path to team A's almacen_*.md
  --team-b NAME     (same for team B)
  --agent-b PATH
  --almacen-b PATH
  --model-a MODEL   Specific LLM for team A 
  --model-b MODEL   Specific LLM for team B

tournament options:
  --agents-dir DIR  Folder with team sub-folders  (default: agentes/)
  --output FILE     Results JSON file  (default: tournament_results.json)
```

---

*Built for the AI Supply Chain Hackathon · April 2026*
