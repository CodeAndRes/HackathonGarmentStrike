"""
config_fast.py
──────────────
Preset values for running Garment Strike with ultra-small local models (e.g. qwen2:0.5b).
Import these constants wherever you create an LLMClient or call run_tournament/run_match.

Usage example:
    from config_fast import FAST
    from core.llm_client import LLMClient
    client = LLMClient(**FAST)
"""

MODEL       = "ollama/qwen2:0.5b"
TEMPERATURE = 0.0
MAX_RETRIES = 1
HISTORY_LEN = 3
MAX_TOKENS  = 80
QUICK_MODE  = True

# Convenience dict – unpack directly into LLMClient()
FAST: dict = {
    "model":       MODEL,
    "temperature": TEMPERATURE,
    "max_retries": MAX_RETRIES,
    "max_tokens":  MAX_TOKENS,
    "quick_mode":  QUICK_MODE,
}
