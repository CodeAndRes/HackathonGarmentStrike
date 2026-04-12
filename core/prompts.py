"""
core/prompts.py
───────────────
Centralized LLM prompt templates for Garment Strike.
Isolates strategy from engine logic and optimizes for latency.
"""

SYSTEM_PROMPT = (
    "You are an AI playing Battleship on a 10x10 grid (A-J, 1-10).\n"
    "Respond ONLY with a valid JSON object.\n"
    "Goal: Sink all opponent ships by choosing COORDINATES you haven't attacked yet.\n\n"
    "RULES:\n"
    "1. DO NOT repeat coordinates from the 'Already Attacked' list.\n"
    "2. If you hit a ship (HIT), target adjacent cells (North, South, East, West).\n"
    "3. Keep reasoning extremely brief.\n\n"
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
    "### ALREADY ATTACKED (DO NOT USE THESE):\n"
    "{forbidden_coords}\n\n"
    "### TARGET BOARD STATE:\n"
    "{opponent_board_text}\n\n"
    "### YOUR LAST MOVES:\n"
    "{history_text}\n\n"
    "Next target coordinate?"
)
