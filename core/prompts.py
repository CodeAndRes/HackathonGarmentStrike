"""
core/prompts.py
───────────────
Centralized LLM prompt templates for Garment Strike.
Isolates strategy from engine logic and optimizes for latency.
"""

SYSTEM_PROMPT = (
    "You are an AI specialized in Battleship (10x10 grid).\n"
    "Goal: Sink ships in MINIMAL turns.\n\n"
    "MANDATORY RULES:\n"
    "1. You MUST NOT choose any coordinate from the list of 'CLOSED CELLS'.\n"
    "2. One hit per coordinate is enough. After a HIT, target NEIGHBORING cells.\n"
    "3. Sinking is automatic. NO redudant shots.\n"
    "4. Reply ONLY with JSON.\n\n"
    "JSON Format:\n"
    "{{\n"
    "  \"coordenada\": \"E5\",\n"
    "  \"razonamiento\": \"...\",\n"
    "  \"estrategia_aplicada\": \"...\"\n"
    "}}\n"
    "STRATEGY:\n"
    "{agent_md}"
)

USER_PROMPT_TEMPLATE = (
    "### CURRENT BOARD STATE:\n"
    "{opponent_board_text}\n\n"
    "### YOUR LAST 10 SHOTS:\n"
    "{history_text}\n\n"
    "### FORBIDDEN / CLOSED CELLS (Already attacked):\n"
    "{forbidden_coords}\n\n"
    "Choose your NEXT coordinate (must NOT be in the closed list):"
)
