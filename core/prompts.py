"""
core/prompts.py
───────────────
Centralized LLM prompt templates for Garment Strike.
Isolates strategy from engine logic and optimizes for latency.
"""

SYSTEM_PROMPT = (
    "You are a Battleship AI (10x10 grid).\n"
    "Goal: Sink ships in MINIMAL turns.\n\n"
    "MANDATORY RULES:\n"
    "1. VALID COORDINATES: Row A-J, Column 1-10 ONLY (e.g., A1, J10).\n"
    "2. NO REPETITION: Never target a coordinate from 'CLOSED CELLS'.\n"
    "3. STRATEGY: One hit per cell is enough. After a HIT, target neighbors.\n"
    "4. Sinking is automatic. NO redundant shots.\n"
    "5. Output ONLY JSON.\n\n"
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
    "### CLOSED CELLS (DO NOT TARGET):\n"
    "{forbidden_coords}\n\n"
    "Command: Choose a new coordinate (A-J, 1-10) not listed above:"
)
