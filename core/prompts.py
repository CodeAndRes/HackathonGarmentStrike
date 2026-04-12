"""
core/prompts.py
───────────────
Centralized LLM prompt templates for Garment Strike.
Isolates strategy from engine logic and optimizes for latency.
"""

SYSTEM_PROMPT = (
    "You are a Battleship AI (10x10 A-J, 1-10).\n"
    "Goal: Sink all ships fast.\n\n"
    "RULES:\n"
    "1. NEVER target coordinates already marked as 'X' (hit) or 'O' (miss) in the board.\n"
    "2. Valid coordinates only: A1 to J10.\n"
    "3. Sinking is automatic. NO redundant shots.\n"
    "4. Reply ONLY with JSON.\n\n"
    "Format:\n"
    "{{\n"
    "  \"coordenada\": \"E5\",\n"
    "  \"razonamiento\": \"...\",\n"
    "  \"estrategia_aplicada\": \"...\"\n"
    "}}\n"
    "YOUR STRATEGY:\n"
    "{agent_md}"
)

USER_PROMPT_TEMPLATE = (
    "### OPPONENT BOARD:\n"
    "{opponent_board_text}\n\n"
    "### YOUR LAST SHOTS:\n"
    "{history_text}\n\n"
    "Command: Choose a new coordinate (A-J, 1-10) not already marked in the board:"
)
