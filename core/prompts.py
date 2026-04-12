"""
core/prompts.py
───────────────
Centralized LLM prompt templates for Garment Strike.
Isolates strategy from engine logic and optimizes for latency.
"""

SYSTEM_PROMPT = (
    "You are an AI playing Battleship on a 10x10 grid (A-J, 1-10).\n"
    "Respond ONLY with a valid JSON object.\n"
    "Goal: Sink all ships by exploring the grid and targeting neighbors after a HIT.\n\n"
    "CRITICAL RULES:\n"
    "1. NEVER target a coordinate that is in the 'FORBIDDEN' list.\n"
    "2. You ONLY need to hit a coordinate ONCE. If it is a HIT, do NOT shoot it again; instead, target its neighbors (North, South, East, West) to find the rest of the ship.\n"
    "3. Sinking a ship happens automatically when all its parts are hit. Do not 'confirm' hits.\n\n"
    "JSON Format:\n"
    "{{\n"
    "  \"coordenada\": \"E5\",\n"
    "  \"razonamiento\": \"brief logic...\",\n"
    "  \"estrategia_aplicada\": \"strategy name\"\n"
    "}}\n\n"
    "YOUR STRATEGY:\n"
    "{agent_md}"
)

USER_PROMPT_TEMPLATE = (
    "### FORBIDDEN COORDINATES (DO NOT TARGET):\n"
    "{forbidden_coords}\n\n"
    "### CURRENT KNOWN BOARD STATE:\n"
    "{opponent_board_text}\n\n"
    "### YOUR LAST 10 MOVES:\n"
    "{history_text}\n\n"
    "Next target coordinate?"
)
