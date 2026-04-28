import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.bracket_engine import BracketEngine
from core.llm_client import LLMClient

def debug():
    engine = BracketEngine()
    engine.load_state()
    
    match_id = "q1"
    print(f"Probando partida {match_id}...")
    
    # Usar modelo offline para no gastar tokens
    client = LLMClient(model="offline")
    
    engine.run_bracket_match(match_id, client)
    
    # Recargar estado
    engine.load_state()
    m = engine.matches[match_id]
    print(f"Estado final: {m.status}")
    print(f"Ganador: {m.winner}")

if __name__ == "__main__":
    debug()
