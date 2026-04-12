"""
core/prompts.py
───────────────
Centralized LLM prompt templates for Garment Strike.
Isolates strategy from engine logic and optimizes for latency.
"""

SYSTEM_PROMPT = (
    "You are an AI playing Battleship on a 10x10 grid (A-J, 1-10).\n"
    "Respond ONLY with a valid JSON object.\n"
    "Keep reasoning extremely brief to ensure fast response times.\n"
    "Coordinates you have already shot and their results are provided.\n"
    "DO NOT repeat coordinates.\n\n"
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
    "OPPONENT BOARD STATE:\n"
    "{opponent_board_text}\n\n"
    "YOUR PREVIOUS SHOTS:\n"
    "{history_text}\n\n"
    "What is your next target coordinate?"
)
