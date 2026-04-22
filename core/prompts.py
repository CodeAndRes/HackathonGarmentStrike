"""
core/prompts.py
───────────────
Centralized LLM prompt templates for Garment Strike.
Isolates strategy from engine logic and optimizes for latency.
"""

SYSTEM_PROMPT = (
    "Battleship AI. {size}x{size} grid. Sink all ships.\n"
    "RULES: No re-shooting X/O cells. Valid: {range_text}. JSON only.\n"
    "{{\"coordenada\":\"E5\",\"razonamiento\":\"...\",\"estrategia_aplicada\":\"...\"}}\n"
    "STRATEGY:\n{agent_md}"
)

USER_PROMPT_TEMPLATE = (
    "{warning_text}"
    "BOARD:\n{opponent_board_text}\n\n"
    "LAST 5:\n{history_text}\n\n"
    "Pick ONE valid coord ({range_text}) not yet shot:"
)
